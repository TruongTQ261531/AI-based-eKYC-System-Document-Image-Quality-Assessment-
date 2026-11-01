import io
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from research.vlm_web import app


class VLMWebTests(unittest.TestCase):
    def test_not_ready_does_not_make_up_model_fields(self):
        with patch('research.vlm_web.deployment',side_effect=ValueError('pending')),TestClient(app,base_url='http://127.0.0.1:8002') as client:
            self.assertFalse(client.get('/api/health').json()['ready'])
            response=client.post('/api/scan',content=b'fake',headers={'Content-Type':'image/png'})
            self.assertEqual(response.status_code,503)

    def test_cross_origin_denied(self):
        with TestClient(app,base_url='http://127.0.0.1:8002') as client:
            response=client.post('/api/scan',content=b'x',headers={'Origin':'https://evil.example','Content-Type':'image/png'})
            self.assertEqual(response.status_code,403)

    def test_camera_fields_are_model_response_not_demo_lookup(self):
        image=Image.new('RGB',(96,72),'white');data=io.BytesIO();image.save(data,format='PNG')
        answer=dict(fields={'full_name':'MODEL OUTPUT'},model='mock',valid_extraction_format=True,
                    generated_tokens=12,inference_seconds=.01,liveness_evaluated=False,identity_approved=False,warnings=[])
        with patch('research.vlm_web.deployment',return_value=({},None)),patch('research.vlm_web.predict_image',return_value=answer),TestClient(app,base_url='http://127.0.0.1:8002') as client:
            response=client.post('/api/scan',content=data.getvalue(),headers={'Content-Type':'image/png'})
            self.assertEqual(response.status_code,200)
            result=response.json();self.assertEqual(result['fields'],{'full_name':'MODEL OUTPUT'})
            self.assertEqual(result['source_dimensions'],[96,72]);self.assertFalse(result['identity_approved'])
            self.assertEqual(response.headers['cache-control'],'no-store')

    def test_invalid_image_has_specific_error(self):
        with patch('research.vlm_web.deployment',return_value=({},None)),TestClient(app,base_url='http://127.0.0.1:8002') as client:
            response=client.post('/api/scan',content=b'not image',headers={'Content-Type':'image/png'})
            self.assertEqual(response.status_code,400)

    def test_demo_has_no_arbitrary_file_access(self):
        with TestClient(app,base_url='http://127.0.0.1:8002') as client:
            self.assertEqual(client.get('/api/specimen/samples.json').status_code,404)
            self.assertEqual(client.get('/assets/secret.txt').status_code,404)

    def test_csp_and_local_camera_policy(self):
        with TestClient(app,base_url='http://127.0.0.1:8002') as client:
            response=client.get('/')
            self.assertEqual(response.status_code,200)
            self.assertIn("connect-src 'self'",response.headers['content-security-policy'])
            self.assertEqual(response.headers['permissions-policy'],'camera=(self), microphone=()')


if __name__=='__main__':unittest.main()
