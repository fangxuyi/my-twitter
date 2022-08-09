from friendships.api.tests import FRIENDSHIP_FOLLOW_URL
from friendships.models import Friendship
from testing.testcases import TestCase
from rest_framework.test import APIClient
from tweets.api.tests import TWEET_CREATE_API

NEWSFEEDS_URL = '/api/newsfeeds/'

class NewsFeedApiTests(TestCase):

    def setUp(self):
        self.user1 = self.create_user("user1")
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user("user2")
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)


    def test_list(self):
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)

        response = self.user1_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)

        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["newsfeeds"]), 0)

        self.user1_client.post(TWEET_CREATE_API, {'content': "Hello World"})
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 1)

        self.user1_client.post(FRIENDSHIP_FOLLOW_URL.format(self.user2.id))
        response = self.user2_client.post(TWEET_CREATE_API, {'content': "Hello World"})
        posted_tweet_id = response.data["id"]
        response = self.user1_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)
