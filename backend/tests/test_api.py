import unittest

from app import create_app


class FlaskTestApi(unittest.TestCase):
    def setUp(self):
        self.app = create_app('test')
        self.client = self.app.test_client(use_cookies=True)
