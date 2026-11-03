"""One diagnostic update under each allocator policy, outside primary budgets."""
import argparse
import os


def main():
    p=argparse.ArgumentParser();p.add_argument('policy',choices=['default','gc']);a=p.parse_args()
    if a.policy=='gc':os.environ['PYTORCH_CUDA_ALLOC_CONF']='garbage_collection_threshold:0.6'
    else:os.environ.pop('PYTORCH_CUDA_ALLOC_CONF',None)
    from research.hp_common import CACHE,CONFIG,OUT,signature,load,save,sha
    from research.hp_study import configure
    from research import vlm_train as trainer
    with trainer.process_lock():
        model,trainer=configure(42);model.offload_vision();model.lora(CONFIG)
        source=CACHE/'training/hard_42/step_0080'
        dest=CACHE/'runtime_parity'/a.policy
        if (dest/'step_0081/complete.json').exists():
            print('HP_PARITY_ALREADY_COMPLETE',a.policy,flush=True);return
        events,_=trainer.train_steps(model,load('train'),[],42,320,4,dest,start_state=source,stop=81,save_every=81)
        save(dest/'run.json',dict(policy=a.policy,allocator_env=os.environ.get('PYTORCH_CUDA_ALLOC_CONF'),signature=signature(),
            checkpoint80_sha256=sha(source/'adapter_model.safetensors'),diagnostic_optimizer_updates=1,
            primary_training_update=False,events=events))
        print('HP_PARITY_UPDATE_DONE',a.policy,flush=True)


if __name__=='__main__':main()
