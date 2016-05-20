import os
import app
import unittest
import tempfile

class HelloWorld(unittest.TestCase):

    def setUp(self):
        self.app = app.app.test_client()

    def test_hello_world(self):
        res = self.app.get('/')
        data = res.data.decode('utf-8')
        assert data == 'Hello World!'

if __name__ == '__main__':
    unittest.main()
