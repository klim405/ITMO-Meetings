import json
import unittest
from datetime import datetime, timedelta

from app import create_app
from app.models.models import User, Sex


class APITestAbstract(unittest.TestCase):
    def setUp(self):
        self.app = create_app('test')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)
        self.token_info = {}
        self.user_credentials = {'username': 'testuser', 'password': 'Test1234'}
        self.staff_credentials = {'username': 'teststaff', 'password': 'Test1234'}
        if User.get_by_login(self.user_credentials['username']) is None:
            User(firstname='dddd', surname='sss', sex=Sex.male, age=12, telephone='+72330988989', email='Test@test.ru',
                 **self.user_credentials).save()
        if User.get_by_login(self.staff_credentials['username']) is None:
            User(firstname='dddd', surname='sss', sex=Sex.male, age=12, telephone='+72340988989', email='Staff@test.ru',
                 is_staff=True, **self.staff_credentials).save()
        self.token_receive_time = datetime.now()

    def get_credentials(self, staff=False):
        return self.staff_credentials if staff else self.user_credentials

    def login(self, *_, staff=False):

        resp = self.post('/api/auth/login', data=self.get_credentials(staff), auth=False)
        self.token_info = json.loads(resp.data)
        self.token_receive_time = datetime.now()

    def get_auth_headers(self):
        if not self.token_info:
            self.login()
        elif self.token_receive_time + timedelta(seconds=self.token_info['expire_in']) < datetime.now():
            resp = self.post('/api/auth/refresh', data=self.token_info, auth=False)
            self.token_info = json.loads(resp.data)
        auth_header = self.token_info['token_type'] + ' ' + self.token_info['access_token']
        headers = {
            'Authorization': auth_header,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        return headers

    def get(self, url, *args, auth=True):
        headers = None
        if auth:
            headers = self.get_auth_headers()
        return self.client.get(
            url,
            headers=headers,
            follow_redirects=True
        )

    def post(self, url, *args, data=None, auth=True):
        data = {} if data is None else data
        headers = None
        if auth:
            headers = self.get_auth_headers()
        return self.client.post(
            url,
            headers=headers,
            data=json.dumps(data),
            content_type='application/json',
            follow_redirects=True
        )

    def put(self, url, *args, data=None, auth=True):
        data = {} if data is None else data
        headers = None
        if auth:
            headers = self.get_auth_headers()
        return self.client.put(
            url,
            headers=headers,
            data=json.dumps(data),
            content_type='application/json',
            follow_redirects=True
        )

    def delete(self, url, *args, data=None, auth=True):
        data = {} if data is None else data
        headers = None
        if auth:
            headers = self.get_auth_headers()
        return self.client.delete(
            url,
            headers=headers,
            data=json.dumps(data),
            content_type='application/json',
            follow_redirects=True
        )

    def assertStatus(self, resp, status_code):
        self.assertEqual(resp.status_code, status_code, msg=f'Asserts status code {status_code}')
