from testing.testcases import TestCase
from rest_framework.test import APIClient
from friendships.models import Friendship

FRIENDSHIP_FOLLOWER_URL = '/api/friendships/{}/followers/'
FRIENDSHIP_FOLLOWING_URL = '/api/friendships/{}/followings/'
FRIENDSHIP_FOLLOW_URL = '/api/friendships/{}/follow/'
FRIENDSHIP_UNFOLLOW_URL = '/api/friendships/{}/unfollow/'

class FriendshipApiTests(TestCase):

    def setUp(self):
        self.anonymous_client = APIClient()

        self.user1  = self.create_user("user1", "user1@twitter.com")
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user("user2", "user2@twitter.com")
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)

        for i in range(2):
            follower = self.create_user('user1_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.user1)
        for i in range(3):
            following = self.create_user('user1_following{}'.format(i))
            Friendship.objects.create(from_user=self.user1, to_user=following)

    def test_follow(self):
        url = FRIENDSHIP_FOLLOW_URL.format(self.user1.id)

        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)

        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, 405)

        response = self.user1_client.post(url)
        self.assertEqual(response.status_code, 400)

        response = self.user2_client.post(url)
        self.assertEqual(response.status_code, 201)

        response = self.user2_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['duplicate'], True)

        count = Friendship.objects.count()
        response = self.user1_client.post(FRIENDSHIP_FOLLOW_URL.format(self.user2.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count+1)


    def test_unfollow(self):
        url = FRIENDSHIP_UNFOLLOW_URL.format(self.user1.id)

        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)

        response = self.user1_client.get(url)
        self.assertEqual(response.status_code, 405)

        response = self.user1_client.post(url)
        self.assertEqual(response.status_code, 400)

        Friendship.objects.create(from_user=self.user2, to_user=self.user1)
        count = Friendship.objects.count()
        response = self.user2_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendship.objects.count(), count-1)

        count = Friendship.objects.count()
        response = self.user2_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendship.objects.count(), count)

    def test_followings(self):
        url = FRIENDSHIP_FOLLOWING_URL.format(self.user1.id)

        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)

        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 3)

        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        ts2 = response.data['followings'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['followings'][0]['user']['username'],
            'user1_following2'
        )
        self.assertEqual(
            response.data['followings'][1]['user']['username'],
            'user1_following1'
        )
        self.assertEqual(
            response.data['followings'][2]['user']['username'],
            'user1_following0'
        )

    def test_followers(self):

        url = FRIENDSHIP_FOLLOWER_URL.format(self.user1.id)

        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)

        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 2)

        ts0 = response.data['followers'][0]['created_at']
        ts1 = response.data['followers'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['followers'][0]['user']['username'],
            'user1_follower1'
        )
        self.assertEqual(
            response.data['followers'][1]['user']['username'],
            'user1_follower0'
        )
