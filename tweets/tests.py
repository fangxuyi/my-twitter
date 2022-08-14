from testing.testcases import TestCase
from django.contrib.auth.models import User
from tweets.models import Tweet
from datetime import timedelta
from utils.time_helpers import utc_now


class TweetsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='user1')
        self.tweet = Tweet.objects.create(user=self.user, content='Lisa testing content')

    def test_hours_to_now(self):
        self.tweet.created_at = utc_now() - timedelta(hours=10)
        self.tweet.save()
        self.assertEqual(self.tweet.hours_to_now, 10)

    def test_like_set(self):
        self.create_like(self.user, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.create_like(self.user, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        user2 = self.create_user('user2')
        self.create_like(user2, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 2)
