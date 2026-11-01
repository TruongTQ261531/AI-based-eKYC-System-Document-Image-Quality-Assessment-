"""Same HTTP contract, explicitly mocked inference; no camera/accuracy claim."""
from unittest.mock import patch
from research import v3_web
from research.tests import test_v2_web

class SourceHTTP(test_v2_web.LocalHTTP):
    def setUp(self):
        self.binding=patch.object(test_v2_web,'web',v3_web);self.binding.start()
        self.addCleanup(self.binding.stop)
        super().setUp()

