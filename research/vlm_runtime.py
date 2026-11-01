"""Local-only Vintern inference and frozen-feature access; no field references."""
import hashlib
import importlib
import json
from pathlib import Path
import sys
import time
import types

import numpy as np
from PIL import Image, ImageOps
import torch

from research.vlm_data import PROMPT
from research.vlm_setup import CACHE, OUT, ROOT, sha, save

PREPROCESS = 'fit_896x448_white_split2_imagenet_v1'


def signature():
    paths=['research/vlm_data.py','research/vlm_runtime.py','research/vlm_train.py',
           'research/VLM_LORA_PROTOCOL.md','research/results/vlm_lora_v1/assets.json',
           'research/results/vlm_lora_v1/dataset_card.json','research/vlm_config.json']
    return hashlib.sha256(json.dumps({p:sha(ROOT/p) for p in paths},sort_keys=True).encode()).hexdigest()


def configure(seed=42):
    import random
    torch.set_num_threads(2)
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if not torch.cuda.is_available(): raise RuntimeError('CUDA unavailable: launch through research.vlm_setup run')
    torch.cuda.manual_seed_all(seed)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.backends.cudnn.deterministic=True
    torch.backends.cudnn.benchmark=False
    torch.use_deterministic_algorithms(True)


def pixels(image):
    image=ImageOps.exif_transpose(image).convert('RGB')
    canvas=ImageOps.pad(image,(896,448),method=Image.Resampling.BICUBIC,color='white',centering=(.5,.5))
    data=np.stack([np.asarray(canvas.crop((x,0,x+448,448))).copy() for x in (0,448)])
    tensor=torch.from_numpy(data).permute(0,3,1,2).float()/255
    return (tensor-torch.tensor([.485,.456,.406])[None,:,None,None])/torch.tensor([.229,.224,.225])[None,:,None,None]


def reviewed_package():
    name='_ekyc_pinned_vintern'
    if name not in sys.modules:
        pkg=types.ModuleType(name); pkg.__path__=[str(CACHE/'model')];sys.modules[name]=pkg
    return importlib.import_module(name+'.modeling_internvl_chat')


class VLM:
    def __init__(self, seed=42):
        start=time.perf_counter()
        configure(seed)
        manifest=json.loads((OUT/'assets.json').read_text(encoding='utf-8'))
        for item in manifest['model']:
            path=CACHE/'model'/item['file']
            if not path.exists(): raise RuntimeError('Model preparation incomplete; run research.vlm_setup model first')
            if item.get('sha256') and sha(path)!=item['sha256']: raise ValueError('Pinned model checksum mismatch')
            if not item.get('sha256'):
                data=path.read_bytes()
                if hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()!=item['git_blob']:
                    raise ValueError('Pinned model source changed')
        from transformers import AutoTokenizer
        upstream=reviewed_package()
        self.dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        self.tokenizer=AutoTokenizer.from_pretrained(str(CACHE/'model'),local_files_only=True,trust_remote_code=False)
        self.model=upstream.InternVLChatModel.from_pretrained(str(CACHE/'model'),
            torch_dtype=self.dtype,low_cpu_mem_usage=True,use_flash_attn=False,local_files_only=True).eval()
        self.model.requires_grad_(False)
        self.context_id=self.tokenizer.convert_tokens_to_ids('<IMG_CONTEXT>')
        self.model.img_context_token_id=self.context_id
        self.upstream=upstream
        self.model.to('cuda')
        self.model_id='original'
        self.cached_vision=False
        self.cold_load_seconds=time.perf_counter()-start
        if not (OUT/'training_environment.json').exists():
            import importlib.metadata as metadata
            import psutil,platform
            props=torch.cuda.get_device_properties(0)
            save(OUT/'training_environment.json',dict(gpu=props.name,gpu_bytes=props.total_memory,
                cuda=torch.version.cuda,torch=torch.__version__,dtype=str(self.dtype),cpu=platform.processor(),
                ram_bytes=psutil.virtual_memory().total,ram_available_at_load=psutil.virtual_memory().available,
                package_versions={k:metadata.version(k) for k in ('torch','torchvision','transformers','peft','accelerate','safetensors','timm')},
                cold_load_seconds=self.cold_load_seconds,model_sha256=next(x['sha256'] for x in manifest['model'] if x['file']=='model.safetensors'),
                source_review='Pinned model Python files inspected; no network/process execution; local config reading only'))

    def prompt_ids(self, patches=2):
        conv=self.upstream.get_conv_template(self.model.template)
        conv.system_message=self.model.system_message
        conv.append_message(conv.roles[0],'<image>\n'+PROMPT)
        conv.append_message(conv.roles[1],None)
        text=conv.get_prompt().replace('<image>','<img>'+'<IMG_CONTEXT>'*(self.model.num_image_token*patches)+'</img>',1)
        return self.tokenizer(text,return_tensors='pt',add_special_tokens=True)['input_ids'], self.tokenizer.convert_tokens_to_ids(conv.sep.strip())

    def features(self, sample):
        from safetensors.torch import load_file,save_file
        path=CACHE/'features'/(hashlib.sha256((PREPROCESS+sample['input_sha256']).encode()).hexdigest()+'.safetensors')
        if path.exists():
            value=load_file(str(path))['features']
            if value.shape!=(2,256,896) or value.dtype!=self.dtype: raise ValueError('Feature cache contract changed')
            return value
        if self.cached_vision: raise ValueError('Missing feature after vision offload')
        source=ROOT/sample['path']
        if sha(source)!=sample['input_sha256']: raise ValueError('Input hash changed')
        with Image.open(source) as im: tensor=pixels(im).to(device='cuda',dtype=self.dtype)
        with torch.no_grad(): value=self.model.extract_feature(tensor).detach().cpu().contiguous()
        path.parent.mkdir(parents=True,exist_ok=True)
        tmp=path.with_suffix('.tmp');save_file({'features':value},str(tmp),metadata={'preprocessing':PREPROCESS,'model_revision':'b98f263eab246eb5269ade64edbdca8a887dc44d'})
        tmp.replace(path)
        return value

    def offload_vision(self):
        self.model.vision_model.to('cpu');self.model.mlp1.to('cpu');self.cached_vision=True
        torch.cuda.empty_cache()

    def embeddings(self, ids, features):
        embed=self.model.language_model.get_input_embeddings()(ids).clone()
        positions=ids.eq(self.context_id)
        if int(positions.sum())!=features.shape[0]*features.shape[1]: raise ValueError('Image token count mismatch')
        embed[positions]=features.to(device=embed.device,dtype=embed.dtype).reshape(-1,embed.shape[-1])
        return embed

    def tokens(self, target):
        ids,eos=self.prompt_ids()
        answer=json.dumps(target,ensure_ascii=False,sort_keys=True,separators=(',',':'))
        tail=self.tokenizer(answer,add_special_tokens=False)['input_ids']+[eos]
        prefix=ids.shape[1]
        joined=torch.cat([ids,torch.tensor([tail],dtype=torch.long)],dim=1)
        labels=joined.clone();labels[:,:prefix]=-100
        return joined,labels

    def loss(self, sample):
        ids,labels=self.tokens(sample['target']);ids=ids.to('cuda');labels=labels.to('cuda')
        embeds=self.embeddings(ids,self.features(sample))
        if self.model.language_model.training: embeds.requires_grad_(True)
        output=self.model.language_model(inputs_embeds=embeds,attention_mask=torch.ones_like(ids),labels=labels,use_cache=False,return_dict=True)
        return output.loss,int(labels.ne(-100).sum()),ids.shape[1]

    def infer_features(self, feature, max_new_tokens=320):
        ids,eos=self.prompt_ids();ids=ids.to('cuda')
        embeds=self.embeddings(ids,feature)
        self.model.language_model.eval()
        with torch.no_grad():
            output=self.model.language_model.generate(inputs_embeds=embeds,attention_mask=torch.ones_like(ids),
                do_sample=False,max_new_tokens=max_new_tokens,eos_token_id=eos,pad_token_id=self.tokenizer.pad_token_id,
                use_cache=True)
        return self.tokenizer.decode(output[0],skip_special_tokens=True).strip(),int(output.shape[1])

    def infer(self,sample):
        import psutil
        torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter()
        feature=self.features(sample);after_feature=time.perf_counter()
        text,count=self.infer_features(feature)
        torch.cuda.synchronize()
        memory=psutil.Process().memory_info()
        return dict(text=text,generated_tokens=count,wall_seconds=time.perf_counter()-start,
                    feature_access_seconds=after_feature-start,
                    peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),
                    process_rss_bytes=memory.rss,process_peak_rss_bytes=getattr(memory,'peak_wset',memory.rss),
                    visual_features_cached=True)

    def lora(self, config):
        from peft import LoraConfig,get_peft_model
        self.model.language_model=get_peft_model(self.model.language_model,LoraConfig(
            r=config['rank'],lora_alpha=config['alpha'],lora_dropout=0.,
            target_modules=['q_proj','k_proj','v_proj','o_proj'],bias='none',task_type='CAUSAL_LM'))
        self.model.language_model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        self.model.language_model.config.use_cache=False
        self.model.language_model.print_trainable_parameters()


def parsed(text):
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result: raise ValueError('Duplicate JSON key')
            result[k]=v
        return result
    try:
        value=json.loads(text,object_pairs_hook=unique)
        if not isinstance(value,dict): return {},False
        if any(not isinstance(k,str) or not isinstance(v,(str,int,float)) or isinstance(v,bool) for k,v in value.items()): return {},False
        return {k:str(v) for k,v in value.items()},True
    except (ValueError,TypeError): return {},False


def normalized(text):
    import unicodedata
    return ' '.join(unicodedata.normalize('NFC',str(text)).upper().split())


def semantic_value(key,value):
    value=normalized(value)
    if key in ('dob','expiry_date'):
        from datetime import datetime
        for fmt in ('%d/%m/%Y','%Y-%m-%d','%d-%m-%Y','%d.%m.%Y'):
            try: return datetime.strptime(value,fmt).strftime('%Y-%m-%d')
            except ValueError: pass
        return None
    if key=='gender':
        return {'M':'NAM','MALE':'NAM','NAM':'NAM','F':'NỮ','FEMALE':'NỮ','NỮ':'NỮ','NU':'NỮ'}.get(value)
    return value


def score(target, prediction, valid):
    correct=sum(k in prediction and semantic_value(k,v) is not None and semantic_value(k,v)==semantic_value(k,prediction[k]) for k,v in target.items())
    literal=sum(k in prediction and normalized(v)==normalized(prediction[k]) for k,v in target.items())
    return dict(correct=correct,reference=len(target),predicted=len(prediction),valid_json=bool(valid),
                literal_correct=literal,
                extra_keys=sum(k not in target for k in prediction),missing_keys=sum(k not in prediction for k in target),
                exact_document=bool(valid and len(prediction)==len(target) and correct==len(target)))


def aggregate(rows):
    c=sum(r['correct'] for r in rows);n=sum(r['reference'] for r in rows);p=sum(r['predicted'] for r in rows)
    return dict(cases=len(rows),correct=c,reference=n,predicted=p,precision=c/max(p,1),recall=c/max(n,1),
                f1=2*c/max(n+p,1),json_valid_rate=sum(r['valid_json'] for r in rows)/max(len(rows),1),
                document_exact_rate=sum(r['exact_document'] for r in rows)/max(len(rows),1),
                extra_keys=sum(r['extra_keys'] for r in rows),missing_keys=sum(r['missing_keys'] for r in rows),
                literal_correct=sum(r['literal_correct'] for r in rows),
                masked_field_outputs=sum(r.get('masked_field_outputs',0) for r in rows))
