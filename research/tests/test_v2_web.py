"""HTTP/privacy contract tests with an explicit fake predictor, not accuracy evidence."""
import io
import unittest
from unittest.mock import patch
from PIL import Image
from fastapi.testclient import TestClient
from research import v2_web as web

class LocalHTTP(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(web.app,base_url='http://127.0.0.1')
        buf=io.BytesIO();Image.new('RGB',(100,80),(200,210,220)).save(buf,format='PNG');self.image=buf.getvalue()
    def test_local_page_has_privacy_and_camera_headers(self):
        r=self.client.get('/');self.assertEqual(r.status_code,200)
        self.assertEqual(r.headers['cache-control'],'no-store');self.assertIn("script-src 'self'",r.headers['content-security-policy'])
        self.assertIn('camera=(self)',r.headers['permissions-policy'])
    def test_foreign_host_is_rejected(self):self.assertEqual(self.client.get('/',headers={'host':'evil.test'}).status_code,400)
    def test_cross_origin_cannot_submit_an_image(self):
        with patch.object(web,'predict') as predict:
            r=self.client.post('/api/scan',content=self.image,headers={'origin':'https://evil.test','content-type':'image/png'})
            self.assertEqual(r.status_code,403);predict.assert_not_called()
    def test_wrong_mime_is_rejected(self):self.assertEqual(self.client.post('/api/scan',content=b'x',headers={'content-type':'text/plain'}).status_code,415)
    def test_unapproved_model_requires_explicit_research_optin(self):
        with patch.object(web,'deployment',return_value=({'deployment_approved':False},None)),patch.object(web,'predict') as predict:
            r=self.client.post('/api/scan',content=self.image,headers={'content-type':'image/png'})
            self.assertEqual(r.status_code,409);predict.assert_not_called()
    def test_optin_passes_actual_decoded_pixels_not_a_dataset_id(self):
        seen=[]
        def fake(image):seen.append(image.shape);return {'fields':{'full_name':'SPECIMEN'},'identity_approved':False}
        with patch.object(web,'deployment',return_value=({'deployment_approved':False},None)),patch.object(web,'predict',side_effect=fake):
            r=self.client.post('/api/scan',content=self.image,headers={'content-type':'image/png','x-research-opt-in':'yes'})
            self.assertEqual(r.status_code,200);self.assertEqual(seen,[(80,100,3)])
            self.assertFalse(r.json()['identity_approved']);self.assertIn('request_processing_wall_seconds',r.json())
    def test_corrupt_image_never_reaches_predictor(self):
        with patch.object(web,'deployment',return_value=({'deployment_approved':True},None)),patch.object(web,'predict') as predict:
            r=self.client.post('/api/scan',content=b'not a png',headers={'content-type':'image/png'})
            self.assertEqual(r.status_code,400);predict.assert_not_called()
    def test_busy_request_is_reported_without_gpu_call(self):
        with patch.object(web,'deployment',return_value=({'deployment_approved':True},None)),patch.object(web,'predict') as predict:
            web.request_lock.acquire()
            try:r=self.client.post('/api/scan',content=self.image,headers={'content-type':'image/png'})
            finally:web.request_lock.release()
            self.assertEqual(r.status_code,429);predict.assert_not_called()
    def test_private_files_are_not_served(self):
        for path in ('/assets/../v2_common.py','/assets/v2_common.py','/api/specimen/../../sources','/api/labels'):
            self.assertEqual(self.client.get(path).status_code,404)

if __name__=='__main__':unittest.main()
