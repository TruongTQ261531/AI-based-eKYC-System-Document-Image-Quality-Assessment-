"""Same HTTP contract, explicitly mocked inference; no camera/accuracy claim."""
from unittest.mock import patch
from research import v3_web
from research.tests import test_v2_web

class SourceHTTP(test_v2_web.LocalHTTP):
    def setUp(self):
        self.binding=patch.object(test_v2_web,'web',v3_web);self.binding.start()
        self.addCleanup(self.binding.stop)
        super().setUp()

    def test_progress_is_numeric_and_exposes_no_private_paths_or_values(self):
        info=v3_web.progress()
        self.assertEqual(info['training_total'],6);self.assertEqual(info['test_total'],1152)
        self.assertTrue(all(isinstance(v,(int,bool)) for v in info.values()))

    def test_unfinished_study_does_not_claim_camera_model_is_ready(self):
        with patch.object(v3_web,'deployment',side_effect=OSError('unfinished')):
            r=self.client.get('/api/health')
            self.assertEqual(r.status_code,200);self.assertFalse(r.json()['ready'])
            self.assertIn('progress',r.json())

