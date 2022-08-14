from testing.testcases import TestCase

LIKE_BASE_URL = '/api/likes/'

class LikeApiTests(TestCase):

    def setUp(self):
        self.user1, self.user1_client = self.create_user_and_client('user1')
        self.user2, self.user2_client = self.create_user_and_client('user2')

    def test_tweet_likes(self):
        tweet = self.create_tweet(self.user1)
        data = {'content_type': 'tweet', 'object_id': tweet.id}

        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        response = self.user1_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        response = self.user1_client.post(LIKE_BASE_URL, {'content_type': 'twet', 'object_id': tweet.id})
        self.assertEqual(response.status_code, 400)

        response = self.user1_client.post(LIKE_BASE_URL, {'content_type': 'tweet', 'object_id': -1})
        self.assertEqual(response.status_code, 400)

        response = self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(tweet.like_set.count(), 1)

        self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.user2_client.post(LIKE_BASE_URL, data)
        self.assertEqual(tweet.like_set.count(), 2)

    def test_tweet_comments(self):
        tweet = self.create_tweet(self.user1)
        comment = self.create_comment(self.user1, tweet)
        data = {'content_type': 'comment', 'object_id': comment.id}

        response = self.anonymous_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 403)

        response = self.user1_client.get(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 405)

        response = self.user1_client.post(LIKE_BASE_URL, {'content_type': 'coment', 'object_id': comment.id})
        self.assertEqual(response.status_code, 400)

        response = self.user1_client.post(LIKE_BASE_URL, {'content_type': 'comment', 'object_id': -1})
        self.assertEqual(response.status_code, 400)

        response = self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)

        self.user1_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 1)
        self.user2_client.post(LIKE_BASE_URL, data)
        self.assertEqual(comment.like_set.count(), 2)