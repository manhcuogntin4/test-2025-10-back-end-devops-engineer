import unittest
from src.app import app, db
from utils.utils import custom_base62_encode, custom_base62_decode
import os

class TestRoutes(unittest.TestCase):
    def setUp(self):
        if not hasattr(app, 'extensions') or 'sqlalchemy' not in app.extensions:
            app.config['TESTING'] = True
            env = 'fincome-db' if os.environ.get('DOCKER_CONTAINER') else 'localhost'
            app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://postgres:password@{env}:5432/mydatabase"
            db.init_app(app)
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = app.test_client()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_custom_base62_encode(self):
        self.assertEqual(custom_base62_encode(0), '0')
        self.assertEqual(custom_base62_encode(10), 'A')
        self.assertEqual(custom_base62_encode(61), 'z')
        self.assertEqual(custom_base62_encode(1000), 'G8')
        
    def test_custom_base62_decode(self):
        self.assertEqual(custom_base62_decode('0'), 0)
        self.assertEqual(custom_base62_decode('A'), 10)
        self.assertEqual(custom_base62_decode('z'), 61)
        self.assertEqual(custom_base62_decode('G8'), 1000)
        
    def test_encode_url(self):
        response = self.client.post('/encode', json={'url': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json, {'short_url': 'http://short.est/1'})

    def test_encode_invalid_url(self):
        response = self.client.post('/encode', json={'url': 'invalid_url'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Not a valid URL.', response.json['url'])
    
    def test_decode_sucess(self):
        response_encode = self.client.post('/encode', json={'url': 'http://example.com'})
        response_decode = self.client.get(f'/decode?short_url={response_encode.json["short_url"]}')
        self.assertEqual(response_decode.status_code, 200)
        self.assertDictEqual(response_decode.json, {'original_url': 'http://example.com'})

    def test_decode_nonexistent_url(self):
        response = self.client.get('/decode?short_url=http://short.est/nonexistent')
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.json, {'error': 'Not Found', 'message': 'Short URL not found'})
    
    def test_encode_url_missing(self):
        response = self.client.get('/decode')
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json, {'error': 'Bad Request', 'message': 'Invalid or missing short URL'})

    def test_encode_url_invalid(self):
        response = self.client.get('/decode?short_url=invalid_url')
        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json, {'error': 'Bad Request', 'message': 'Invalid or missing short URL'})


if __name__ == '__main__':
    unittest.main()