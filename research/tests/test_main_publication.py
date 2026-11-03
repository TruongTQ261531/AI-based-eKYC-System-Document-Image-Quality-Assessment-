"""Publishing must work with only main, retaining staging and privacy guards."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from research import v2_publish, v3_publish


class MainOnlyPublication(unittest.TestCase):
    def fake_git(self, branch='main', staged=b''):
        tip='a'*40
        def invoke(*args):
            if args == ('branch','--show-current'):return branch.encode()
            if args == ('diff','--cached','--name-only'):return staged
            if args == ('rev-parse','HEAD'):return tip.encode()
            if args[:2] == ('ls-remote','origin'):return (tip+'\trefs/heads/main\n').encode()
            return b''
        return invoke

    def test_r2_final_can_publish_on_main_without_research_branch(self):
        with patch.object(v2_publish,'git',side_effect=self.fake_git()) as git, \
             patch.object(v2_publish,'preserve_v1'), \
             patch.object(v2_publish.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
            v2_publish.publish('final')
            git.assert_any_call('push','origin','main')
            paths=next(c.args[2:] for c in git.call_args_list if c.args[:2]==('add','--'))
            self.assertFalse(any(p.startswith(('research/cache/','research/data/')) for p in paths))
            self.assertFalse(any(p.endswith('.safetensors') for p in paths))

    def test_source_final_can_publish_on_main_without_research_branch(self):
        with patch.object(v3_publish,'git',side_effect=self.fake_git()) as git, \
             patch.object(v3_publish,'publish_r2') as r2, \
             patch.object(v3_publish,'preserve_v1'), \
             patch.object(v3_publish.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
            v3_publish.publish('final')
            r2.assert_called_once_with('final')
            git.assert_any_call('push','origin','main')

    def test_unrelated_staged_file_still_blocks_publication(self):
        with patch.object(v2_publish,'git',side_effect=self.fake_git(staged=b'private.env\n')) as git, \
             patch.object(v2_publish,'preserve_v1'):
            with self.assertRaisesRegex(ValueError,'Non-V2 staged files'):
                v2_publish.publish('final')
            self.assertFalse(any(c.args[:1]==('push',) for c in git.call_args_list))

    def test_other_branch_is_rejected_before_staging_or_network(self):
        with patch.object(v2_publish,'git',side_effect=self.fake_git(branch='unreviewed')) as git, \
             patch.object(v2_publish,'preserve_v1'):
            with self.assertRaisesRegex(ValueError,'different branch'):
                v2_publish.publish('final')
            self.assertFalse(any(c.args[:1] in [('add',),('push',)] for c in git.call_args_list))


if __name__=='__main__':unittest.main()
