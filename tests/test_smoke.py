import unittest

from backend import create_app


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_login_page_renders(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_agent_endpoint_supports_summary(self):
        response = self.client.get('/api/ask?q=today%27s%20summary')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get('answer'))


if __name__ == '__main__':
    unittest.main()
