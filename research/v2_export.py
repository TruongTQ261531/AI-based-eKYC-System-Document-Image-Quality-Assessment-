"""Copy the selected small adapter locally; never upload weights or model data."""
import shutil
from research.v2_common import *

def export():
    lock=read(OUT/'test_lock.json');key=lock['selected_model'];source=ROOT/lock['models'][key]['path']
    if read(OUT/'audit.json')['status']!='passed':raise ValueError('Export requires the completed audit')
    dest=CACHE/'export'/key;dest.mkdir(parents=True,exist_ok=True);hashes={}
    for name in ('adapter_config.json','adapter_model.safetensors'):
        digest=sha(source/name)
        if (dest/name).exists() and sha(dest/name)!=digest:raise ValueError('Existing export differs; retain both versions')
        shutil.copyfile(source/name,dest/name);hashes[name]=digest
    base=read(ROOT/'research/results/vlm_lora_v1/assets.json')
    manifest=dict(signature=signature(),selected_model=key,profile=lock['profile'],adapter_sha256=hashes,
        base_model=base['model_id'],base_revision=base['revision'],
        base_weights_sha256=next(r['sha256'] for r in base['model'] if r['file']=='model.safetensors'),
        apply_adapter_to='Vintern.model.language_model; full Vintern vision/projector required',
        tokenizer='Use the pinned full Vintern tokenizer and V2 image-token prompt',
        peft_base_name_is_not_a_standalone_multimodal_model=True,merged_full_model=False,
        weights_uploaded=False,private_labels_copied=False,new_virtualenv=False)
    save(dest/'model_manifest.json',manifest)
    (dest/'README.txt').write_text('This is a LoRA language-module adapter, not a standalone LLM/VLM.\n'
        'Load the complete pinned Vintern-1B-v3_5 first, then PeftModel.from_pretrained(model.language_model, adapter_path).\n'
        'Keep its frozen vision encoder/projector and tokenizer. Use the V2 prompt and locked preprocessing profile.\n'
        'The Qwen base name in PEFT metadata alone cannot read images. No optimizer, dataset or camera data is exported.\n'
        'Launch the repository start-vlm-v2.ps1 for the local application.\n',encoding='utf-8',newline='\n')
    save(OUT/'export.json',dict(directory=dest.relative_to(ROOT).as_posix(),**manifest))
    print('V2_LOCAL_EXPORT',key,flush=True)

if __name__=='__main__':export()
