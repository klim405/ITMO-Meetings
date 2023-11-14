from tests.api import APITestAbstract


class AuthTest(APITestAbstract):
    def setUp(self):
        super(AuthTest, self).setUp()
        self.app_context.push()
    
    def test_login(self):
        resp = self.post('/api/auth/login', data=self.user_credentials, auth=False)
        self.assertStatus(resp, 201)
        self.assertIsNotNone(resp.json.get('access_token', None))

    def test_refresh(self):
        resp1 = self.post('/api/auth/login', data=self.user_credentials, auth=False)
        self.assertStatus(resp1, 201)

        resp2 = self.post('/api/auth/refresh', data=resp1.json, auth=False)
        self.assertStatus(resp2, 201)
        self.assertNotEqual(resp1.json, resp2.json)

    def test_logout(self):
        self.login()
        resp = self.post('/api/auth/logout', data={})
        self.assertStatus(resp, 400)
        resp = self.post('/api/auth/logout', data={'access_token': ',l,'})
        self.assertStatus(resp, 400)
        resp = self.post('/api/auth/logout', data=self.token_info)
        self.assertStatus(resp, 200)
        resp = self.post('/api/auth/logout', data=self.token_info)
        self.assertStatus(resp, 401)
        resp2 = self.post('/api/auth/logout-anywhere')
        self.assertStatus(resp2, 401)

        self.login()
        resp2 = self.post('/api/auth/logout-anywhere')
        self.assertStatus(resp2, 200)
        self.login()
