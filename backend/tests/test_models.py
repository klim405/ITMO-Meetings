import json
import unittest
import uuid

from app import create_app
from app.api.forms import RegistrationUserForm
from app.models.models import User, Sex, AuthTokenError, AuthToken


class ModelsTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('test')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)
        self.user_data = {'firstname': 'Jonh', 'surname': 'Watson', 'sex': Sex.male, 'age': 35,
                          'telephone': '+79221231237', 'email': 'watson@gmail.com', 'password': '12fgG123'}
        self.user_data_wrong = {'firstname': 'Jonh234', 'surname': 'Watson fff', 'sex': Sex.male, 'age': -200,
                                'telephone': '+731237', 'email': 'watson@gmail.co8m', 'password': '12345678'}

    def create_and_get_user(self):
        u = User(**self.user_data)
        u.save()
        return u

    def test_create_delete_user(self):
        u = self.create_and_get_user()
        self.assertIsNotNone(u.id)
        u.delete()

    def test_user_password(self):
        u = self.create_and_get_user()
        pwd = '12345678'
        u.password = pwd
        u.save()
        self.assertTrue(u.verify_password(pwd))
        u.delete()

    def test_delete_user(self):
        u = self.create_and_get_user()
        u.delete()
        self.assertIsNone(User.query.filter_by(email=self.user_data['email']).first())

    def test_auth_token(self):
        u = self.create_and_get_user()
        token = u.gen_auth_token()
        self.assertIsNotNone(AuthToken.get(token.access_token))
        self.assertIsNone(AuthToken.get(uuid.uuid4()))
        token.user.delete()

    def test_gen_token(self):
        u = self.create_and_get_user()
        u.gen_auth_token()
        token = u.gen_auth_token()
        self.assertIsNotNone(token.access_token)
        self.assertIsNotNone(token.refresh_token)
        self.assertTrue(token.is_refresh_available)
        self.assertTrue(token.is_active())
        u.deactivate_all_auth_tokens()
        for tok in u.auth_tokens:
            self.assertFalse(tok.is_active())
        token.user.delete()

    def test_refresh_token(self):
        u = self.create_and_get_user()
        token = u.gen_auth_token()
        self.assertRaises(AuthTokenError, token.refresh, token.access_token)
        token2 = token.refresh(token.refresh_token)
        self.assertFalse(token.is_active())
        self.assertRaises(AuthTokenError, token.refresh, token.refresh_token)
        self.assertTrue(token2.is_active())
        self.assertEqual(token.user, token2.user)
        u.delete()

    def test_json_mixin(self):
        u = self.create_and_get_user()
        uuid_test = uuid.uuid4()
        try:
            auth_token = AuthToken()
            auth_token.from_json(json.dumps({
                'access_token': str(uuid_test),
                'user_id': u.id
            }))
            auth_token.save()
            self.assertEqual(auth_token.access_token, uuid_test, 'Десериализованный токен не совпадает с установленным')
            auth_token.delete()
        finally:
            u.delete()

    def test_user_form(self):
        form = RegistrationUserForm(self.user_data)
        form.validate()
        self.assertTrue(form.validate())
        u = form.save()
        u.delete()

    def test_invalid_user_form(self):
        form = RegistrationUserForm(self.user_data_wrong)
        self.assertFalse(form.validate())
        print(form.get_errors())
