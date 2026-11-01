"""V2 prompt/tiles on the unchanged pinned V1 base loader and LoRA implementation."""
import hashlib
import json
import time
import torch
from PIL import Image
from research.vlm_runtime import VLM as FrozenVLM,aggregate
from research.v2_metrics import score
from research.vlm_analysis import tolerant
from research.v2_common import ROOT,CACHE,DATA,OUT,PILOT_CACHE,PROMPT,CONFIG,sha,save
from research.v2_inputs import Views,pixels

class VLM(FrozenVLM):
    def __init__(self,seed=42,profile='raw2'):
        super().__init__(seed);self.profile=profile;self.views=Views()
        self.input_version=hashlib.sha256((sha(ROOT/'research/v2_inputs.py')+profile).encode()).hexdigest()

    def prompt_ids(self,patches=None):
        patches=patches or (4 if self.profile.endswith('4') else 2)
        conv=self.upstream.get_conv_template(self.model.template);conv.system_message=self.model.system_message
        conv.append_message(conv.roles[0],'<image>\n'+PROMPT);conv.append_message(conv.roles[1],None)
        text=conv.get_prompt().replace('<image>','<img>'+'<IMG_CONTEXT>'*(self.model.num_image_token*patches)+'</img>',1)
        return self.tokenizer(text,return_tensors='pt',add_special_tokens=True)['input_ids'],self.tokenizer.convert_tokens_to_ids(conv.sep.strip())

    def features(self,sample):
        from safetensors.torch import load_file,save_file
        key=hashlib.sha256((self.input_version+sample['input_sha256']).encode()).hexdigest()
        path=CACHE/'features'/self.profile/(key+'.safetensors')
        prior=PILOT_CACHE/'features'/self.profile/(key+'.safetensors')
        if not path.exists() and prior.exists():
            import shutil
            path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(prior,path)
            if prior.with_suffix('.json').exists():shutil.copyfile(prior.with_suffix('.json'),path.with_suffix('.json'))
        n=4 if self.profile.endswith('4') else 2
        if path.exists():
            value=load_file(str(path))['features']
            if value.shape!=(n,256,896) or value.dtype!=self.dtype:raise ValueError('V2 feature contract changed')
            return value
        if self.cached_vision:raise ValueError('Missing feature after offload')
        source=ROOT/sample['path']
        if sha(source)!=sample['input_sha256']:raise ValueError('V2 image changed')
        with Image.open(source) as im:
            image,meta=self.views.prepare(im,self.profile);tensor=pixels(image,self.profile).to(device='cuda',dtype=self.dtype)
        with torch.no_grad():value=self.model.extract_feature(tensor).detach().cpu().contiguous()
        path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
        save_file({'features':value},str(tmp),metadata={'input_version':self.input_version,'input_sha256':sample['input_sha256']});tmp.replace(path)
        save(path.with_suffix('.json'),meta)
        return value

    def infer(self,sample):
        import psutil
        torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter()
        feature=self.features(sample);end_feature=time.perf_counter()
        text,count=self.infer_features(feature,CONFIG['generation_max_new_tokens']);torch.cuda.synchronize()
        return dict(text=text,generated_tokens=count,wall_seconds=time.perf_counter()-start,
            feature_access_seconds=end_feature-start,profile=self.profile,
            peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            process_rss_bytes=psutil.Process().memory_info().rss,visual_features_cached=True)

    def fresh(self,image):
        start=time.perf_counter();view,meta=self.views.prepare(image,self.profile)
        tensor=pixels(view,self.profile).to(device='cuda',dtype=self.dtype)
        torch.cuda.synchronize();before=time.perf_counter()
        with torch.no_grad():feature=self.model.extract_feature(tensor)
        torch.cuda.synchronize();visual=time.perf_counter()-before
        text,count=self.infer_features(feature,CONFIG['generation_max_new_tokens']);torch.cuda.synchronize()
        return dict(text=text,generated_tokens=count,wall_seconds=time.perf_counter()-start,
                    fresh_visual_seconds=visual,visual_features_cached=False,**meta)

def scoring(sample,text):
    fields,parser=tolerant(text);result=score(sample['target'],fields,parser['syntax_object_success'],sample.get('accepted_values'))
    result['unsupported_nonempty']=sum(k not in sample['target'] for k in fields)
    result['wrong_visible_values']=sum(k in fields for k in sample['target'])-result['correct']
    result['visible_omissions']=sum(k not in fields for k in sample['target'])
    masked_keys={f['key'] for f in sample['fields'] if f.get('occluded',False)}
    result['masked_field_outputs']=sum(k not in sample['target'] and k in fields for k in masked_keys)
    result['empty_reference']=not sample['target']
    result['correct_empty_abstention']=not sample['target'] and not fields and parser['syntax_object_success']
    from research.vlm_runtime import parsed
    strict,valid=parsed(text);result['strict']=score(sample['target'],strict,valid,sample.get('accepted_values'))
    return dict(result,**parser),fields

def summary(rows):
    base=aggregate(rows)
    base.update({k:sum(r[k] for r in rows) for k in ('unsupported_nonempty','wrong_visible_values','visible_omissions',
        'correct_empty_abstention','empty_reference','hit_token_limit')})
    base['retake_proxy_rate']=sum(r['predicted']==0 or not r['valid_json'] for r in rows)/max(len(rows),1)
    return base
