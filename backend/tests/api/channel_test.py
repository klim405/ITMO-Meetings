from tests.api import APITestAbstract


class ChannelViewsTest(APITestAbstract):
    def setUp(self):
        super(ChannelViewsTest, self).setUp()
        self.app_context.push()

    def test_create_delete_channel(self):
        resp1 = self.post('/api/channel/', data={'name': 'test channel name'})
        self.assertStatus(resp1, 201)
        channel_id = resp1.json['object']['id']
        resp2 = self.delete(f'/api/channel/{channel_id}')
        self.assertStatus(resp2, 200)

    def test_update_channel(self):
        resp1 = self.post('/api/channel/', data={'name': 'test channel name'})
        self.assertStatus(resp1, 201)
        channel_id = resp1.json['object']['id']
        resp2 = self.put(f'/api/channel/{channel_id}', data={'name': 'test new name'})
        self.assertStatus(resp2, 200)
        resp3 = self.delete(f'/api/channel/{channel_id}')
        self.assertStatus(resp3, 200)

    def test_channel_member_list(self):
        resp1 = self.post('/api/channel/', data={'name': 'test channel name'})
        self.assertStatus(resp1, 201)

        channel_id = resp1.json['object']['id']
        resp2 = self.get(f'/api/channel/{channel_id}/member/list/')
        print(resp2.json)
        self.assertStatus(resp2, 200)
        resp3 = self.delete(f'/api/channel/{channel_id}')
        self.assertStatus(resp3, 200)


