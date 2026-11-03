import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from research import fc_io
from research.fc_common import CACHE, read


class TransientMetadataWrites(unittest.TestCase):
    def folder(self):
        root=CACHE/'test_tmp';root.mkdir(parents=True,exist_ok=True)
        return tempfile.TemporaryDirectory(dir=root)

    def test_transient_lock_retries_without_changing_payload(self):
        with self.folder() as folder:
            dest=Path(folder)/'progress.json';payload={'step':56,'source':'unit-test'};calls=[]
            def sometimes(path,value):
                calls.append(value.copy())
                if len(calls)<3:raise PermissionError('simulated sharing violation')
                return original(path,value)
            original=fc_io.original_save
            with patch.object(fc_io,'original_save',side_effect=sometimes),patch.object(fc_io.time,'sleep'):
                fc_io.save_retry(dest,payload)
            self.assertEqual(read(dest),payload)
            self.assertEqual(calls,[payload]*3)

    def test_permanent_lock_is_reported_after_bounded_retries(self):
        with self.folder() as folder,patch.object(fc_io,'original_save',side_effect=PermissionError('locked')) as writer,patch.object(fc_io.time,'sleep'):
            with self.assertRaises(PermissionError):fc_io.save_retry(Path(folder)/'progress.json',{'step':1})
            self.assertEqual(writer.call_count,8)

    def test_other_failures_are_not_swallowed_or_retried(self):
        with self.folder() as folder,patch.object(fc_io,'original_save',side_effect=ValueError('invalid')) as writer,patch.object(fc_io.time,'sleep'):
            with self.assertRaises(ValueError):fc_io.save_retry(Path(folder)/'progress.json',{'step':1})
            self.assertEqual(writer.call_count,1)


if __name__=='__main__':unittest.main()
