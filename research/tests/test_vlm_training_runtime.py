"""Small CPU checks of the optional training stack, separate from GPU evidence."""
import importlib.util
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import torch


@unittest.skipUnless(importlib.util.find_spec('peft'), 'Optional training cache is not active')
class TrainingRuntimeTests(unittest.TestCase):
    def model(self):
        from transformers import Qwen2Config,Qwen2ForCausalLM
        from peft import get_peft_model,LoraConfig
        torch.manual_seed(17)
        config=Qwen2Config(vocab_size=64,hidden_size=16,intermediate_size=32,num_hidden_layers=1,
                           num_attention_heads=2,num_key_value_heads=2,max_position_embeddings=64)
        native=Qwen2ForCausalLM(config)
        return get_peft_model(native,LoraConfig(r=2,lora_alpha=4,lora_dropout=0.,
            target_modules=['q_proj','k_proj','v_proj','o_proj'],task_type='CAUSAL_LM'))

    def update(self,model,optimizer):
        optimizer.zero_grad(set_to_none=True)
        out=model(input_ids=torch.tensor([[1,2,3,4]]),labels=torch.tensor([[-100,-100,3,4]]))
        out.loss.backward();optimizer.step()
        return float(out.loss.detach())

    def test_real_lora_update_leaves_base_frozen(self):
        model=self.model()
        before={n:p.detach().clone() for n,p in model.named_parameters()}
        optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=.01)
        self.update(model,optimizer)
        changed=[n for n,p in model.named_parameters() if not torch.equal(before[n],p)]
        self.assertTrue(changed)
        self.assertTrue(all('lora_' in n for n in changed))

    def test_answer_only_loss_matches_explicit_causal_ce(self):
        model=self.model().eval();ids=torch.tensor([[1,2,3,4]])
        labels=torch.tensor([[-100,-100,3,4]])
        result=model(input_ids=ids,labels=labels)
        expected=torch.nn.functional.cross_entropy(result.logits[0,1:3],torch.tensor([3,4]))
        self.assertTrue(torch.allclose(result.loss,expected,atol=1e-6))

    def test_checkpoint_restores_optimizer_and_exact_next_update(self):
        from research.vlm_train import checkpoint,restore
        model=self.model();wrapped=types.SimpleNamespace(model=types.SimpleNamespace(language_model=model))
        params=[p for p in model.parameters() if p.requires_grad]
        optimizer=torch.optim.AdamW(params,lr=.01,foreach=False)
        self.update(model,optimizer)
        with tempfile.TemporaryDirectory(dir=Path('research/cache/vlm_lora_v1')) as directory:
            path=Path(directory)
            self.assertTrue(path.resolve().is_relative_to(Path('research/cache/vlm_lora_v1').resolve()))
            with patch('torch.cuda.get_rng_state_all',return_value=[]):
                checkpoint(wrapped,optimizer,1,1,17,2,path,'tiny_cpu_unit_test')
            self.update(model,optimizer)
            expected={n:p.detach().clone() for n,p in model.named_parameters()}
            with patch('torch.cuda.set_rng_state_all'):
                state=restore(wrapped,optimizer,path,'tiny_cpu_unit_test')
            self.assertEqual(state['step'],1)
            self.update(model,optimizer)
            self.assertTrue(all(torch.equal(expected[n],p) for n,p in model.named_parameters()))


if __name__=='__main__':unittest.main()
