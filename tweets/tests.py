from django.test import TestCase
from django.contrib.auth.models import User
from tweets.models import Tweet
from datetime import timedelta
from utils.time_helpers import utc_now


class TweetsTests(TestCase):

    def test_hours_to_now(self):
        lisayi = User.objects.create_user(username='lisayi')
        tweet = Tweet.objects.create(user=lisayi, content='Lisa testing content')
        tweet.created_at = utc_now() - timedelta(hours=10)
        tweet.save()
        self.assertEqual(tweet.hours_to_now, 10)


