from flask import g

from app.models.models import User
from tests.api import APITestAbstract


class UserTest(APITestAbstract):
    def setUp(self):
        super(UserTest, self).setUp()
        self.app_context.push()

    def test_get_current_user(self):
        resp = self.get('/api/user')
        self.assertStatus(resp, 200)

    def test_get_user(self):
        user_id = self.get('/api/user/').json['object']['id']
        resp1 = self.get(f'/api/user/{user_id}')
        self.assertStatus(resp1, 200)

        # Проверка изменения
        resp2 = self.put(f'/api/user/{user_id}', data=resp1.json['object'])
        self.assertStatus(resp2, 200)

        # Проверка на несуществующего пользователя
        resp3 = self.get(f'/api/user/1000000/')
        self.assertStatus(resp3, 404)

        # Проверка на доступ к чужому пользователю пользователя
        staff_user_id = User.query.filter_by(is_staff=True).first().id
        resp4 = self.get(f'/api/user/{staff_user_id}')
        print(resp4.json)
        self.assertStatus(resp4, 200)

        # Проверка изменения чужого пользователя
        resp5 = self.put(f'/api/user/{staff_user_id}', data=resp1.json['object'])
        self.assertStatus(resp5, 403)

        # Само-удаление
        resp6 = self.delete(f'/api/user/{user_id}')
        self.assertStatus(resp6, 200)

        # Проверка изменения админом чужого пользователя
        self.login(staff=True)
        resp7 = self.put(f'/api/user/{user_id}', data=resp1.json['object'])
        self.assertStatus(resp7, 200)
        self.login()






