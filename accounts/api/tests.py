from accounts.models import UserProfile
from django.core.files.uploadedfile import SimpleUploadedFile
from testing.testcases import TestCase
from rest_framework.test import APIClient


#looking for all child classes of TestCase when executed
#all method names starting with test are getting covered
#setup function is getting executed with each test function

LOGIN_URL = '/api/accounts/login/'
LOGOUT_URL = '/api/accounts/logout/'
SIGNUP_URL = '/api/accounts/signup/'
LOGIN_STATUS_URL = '/api/accounts/login_status/'
USER_PROFILE_DETAIL_URL = '/api/profiles/{}/'


class AccountApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user(
            username='admin',
            email='admin@twitter.com',
            password='correct password',
        )

    def test_login(self):
        #This api only takes post. Test expected to fail
        response = self.client.get(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 405)
        #wrong password with post
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'wrong password',
        })
        self.assertEqual(response.status_code, 400)
        #wrong username with post
        response = self.client.post(LOGIN_URL, {
            'username': 'wrong username',
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data['errors']['username'][0]), 'User does not exist.')
        #not logged in
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)
        #logging in
        response = self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data['user'], None)
        self.assertEqual(response.data['user']['id'], self.user.id)

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

    def test_logout(self):

        self.client.post(LOGIN_URL, {
            'username': self.user.username,
            'password': 'correct password',
        })

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], False)

    def test_signup(self):
        data = {
            'username': 'someone',
            'email': 'someone@twitter.com',
            'password': 'any password',
        }

        response = self.client.get(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 405)

        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'not a correct email',
            'password': 'any password'
        })
        self.assertEqual(response.status_code, 400)

        response = self.client.post(SIGNUP_URL, {
            'username': 'someone',
            'email': 'someone@twitter.com',
            'password': '123',
        })
        self.assertEqual(response.status_code, 400)

        response = self.client.post(SIGNUP_URL, {
            'username': 'username is tooooooooooooooooo loooooooong',
            'email': 'someone@twitter.com',
            'password': 'any password',
        })
        self.assertEqual(response.status_code, 400)


        response = self.client.post(SIGNUP_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['username'], 'someone')

        created_user_id = response.data['user']['id']
        profile = UserProfile.objects.filter(user_id=created_user_id).first()
        self.assertNotEqual(profile, None)

        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.data['has_logged_in'], True)

class UserProfileAPITests(TestCase):

    def test_update(self):

        user1, user1_client = self.create_user_and_client('user1')
        p = user1.profile
        p.nickname = 'old nickname'
        p.save()
        url = USER_PROFILE_DETAIL_URL.format(p.id)

        response = self.anonymous_client.put(url, {
            'nickname': 'new nickname',
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data['detail']), 'Authentication credentials were not provided.')
        p.refresh_from_db()
        self.assertEqual(p.nickname, 'old nickname')

        _, user2_client = self.create_user_and_client('user2')
        response = user2_client.put(url, {
            'nickname': 'new nickname',
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data['detail']), 'you do no have permission to access this object.')
        p.refresh_from_db()
        self.assertEqual(p.nickname, 'old nickname')

        response = user1_client.put(url, {
            'nickname': 'new nickname',
        })
        self.assertEqual(response.status_code, 200)
        p.refresh_from_db()
        self.assertEqual(p.nickname, 'new nickname')

        response = user1_client.put(url, {
            'avatar': SimpleUploadedFile(
                name="my-avatar.jpg",
                content=str.encode('a fake image'),
                content_type='image/jpeg',
            )
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual('my-avatar' in response.data['avatar'], True)
        p.refresh_from_db()
        self.assertIsNotNone(p.avatar, None)