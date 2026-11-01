"""Export ONLY the selected adapter and an explicit Vintern-submodule descriptor."""
import json
import shutil

from research.vlm_setup import CACHE,ROOT,OUT,save,sha,MODEL_ID,REVISION


def main():
    lock=json.loads((OUT/'test_lock.json').read_text(encoding='utf-8'))
    seed=lock['selected_model'].split('_')[1];record=lock['adapters'][seed]
    source=(ROOT/record['selected_checkpoint']).resolve()
    target=(CACHE/'export'/lock['selected_model']).resolve()
    if not source.is_relative_to(CACHE.resolve()) or not target.is_relative_to(CACHE.resolve()):raise ValueError('Export path escapes cache')
    if sha(source/'adapter_model.safetensors')!=record['selected_adapter_sha256']:raise ValueError('Adapter changed')
    target.mkdir(parents=True,exist_ok=True)
    for name in ('adapter_model.safetensors','adapter_config.json'):
        temporary=target/(name+'.tmp');shutil.copyfile(source/name,temporary);temporary.replace(target/name)
        if sha(target/name)!=sha(source/name):raise ValueError('Export differs')
    assets=json.loads((OUT/'assets.json').read_text(encoding='utf-8'))
    descriptor=dict(model_id=MODEL_ID,revision=REVISION,scope='language_model submodule of full Vintern VLM',
        base_weights_sha256=next(x['sha256'] for x in assets['model'] if x['file']=='model.safetensors'),
        adapter_sha256=record['selected_adapter_sha256'],selected_model=lock['selected_model'],
        study_signature=lock['signature'],deployment_approved_on_development=lock['deployment_approved'],
        loader='research.vlm_runtime.VLM() then PeftModel.from_pretrained(vlm.model.language_model, adapter_path, is_trainable=False)',
        standalone_text_qwen_loader_is_not_equivalent=True,synthetic_only_finetuning=True,
        model_and_code_license='MIT; generated specimen images CC BY4.0',
        no_identity_or_liveness_approval=True)
    save(target/'vintern_adapter.json',descriptor)
    (target/'README.txt').write_text('This is a language-submodule LoRA for the pinned full Vintern model.\n'
        'Use the project VLM loader; do not treat adapter_config base text-model metadata as a standalone VLM.\n'
        'Base weights/tokenizer/custom source are still required. No optimizer state is needed for inference.\n'
        'Full resumable optimizer/RNG checkpoints remain in the original seed folder.\n'
        'Synthetic-only research pilot; not identity or liveness approval.\n',encoding='ascii')
    save(OUT/'adapter_export.json',dict(**descriptor,export_directory=target.relative_to(ROOT).as_posix(),
        files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in target.iterdir() if p.is_file()}))
    print('EXPORTED',str(target),flush=True)


if __name__=='__main__':main()
