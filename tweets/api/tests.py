from django.core.files.uploadedfile import SimpleUploadedFile
from testing.testcases import TestCase
from rest_framework.test import APIClient
from tweets.models import Tweet, TweetPhoto
from utils.paginations import EndlessPagination

TWEET_LIST_API = '/api/tweets/'
TWEET_CREATE_API = '/api/tweets/'
TWEET_RETRIEVE_API = '/api/tweets/{}/'

class TweetApiTests(TestCase):

    def setUp(self):

        self.user1  = self.create_user("user1", "user1@twitter.com")
        self.tweets1 = [
            self.create_tweet(self.user1)
            for i in range(3)
        ]
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user("user2", "user2@twitter.com")
        self.tweets2 = [
            self.create_tweet(self.user2)
            for i in range(2)
        ]

    def test_list_api(self):
        #get method has to have user_id
        response = self.anonymous_client.get(TWEET_LIST_API)
        self.assertEqual(response.status_code, 400)

        #usual request
        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)

        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user2.id})
        self.assertEqual(len(response.data['results']), 2)

        #test order by: recently posted tweets are displayed first
        self.assertEqual(response.data['results'][0]['id'], self.tweets2[1].id)
        self.assertEqual(response.data['results'][1]['id'], self.tweets2[0].id)

    def test_create_api(self):
        #has to log in
        response = self.anonymous_client.post(TWEET_LIST_API)
        self.assertEqual(response.status_code, 403)

        #has to have content
        response = self.user1_client.post(TWEET_LIST_API)
        self.assertEqual(response.status_code, 400)
        #content cannot be too short
        response = self.user1_client.post(TWEET_LIST_API, {'content': '1'})
        self.assertEqual(response.status_code, 400)
        #content cannot be too long
        response = self.user1_client.post(TWEET_LIST_API, {
            'content': '1' * 141
        })
        self.assertEqual(response.status_code, 400)

        #normal posting
        tweets_count = Tweet.objects.count()
        response = self.user1_client.post(TWEET_CREATE_API, {
            "content": "Hello World, this is my first tweet!"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(Tweet.objects.count(), tweets_count + 1)

    def test_retrieve(self):
        url = TWEET_RETRIEVE_API.format(-1)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 404)

        tweet = self.create_tweet(self.user1)
        url = TWEET_RETRIEVE_API.format(tweet.id)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["comments"]), 0)

        self.create_comment(self.user2, tweet, 'holly s**')
        self.create_comment(self.user1, tweet, 'hmm...')
        self.create_comment(self.user1, self.create_tweet(self.user2), 'hmm....')
        response = self.anonymous_client.get(url)
        self.assertEqual(len(response.data['comments']), 2)

    def test_create_with_files(self):
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'a selfie',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 0)

        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'a selfie',
            'files': [],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 0)

        file = SimpleUploadedFile(
            name='selfie.jpg',
            content=str.encode('a fake image'),
            content_type='image/jpeg',
        )
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'a selfie',
            'files': [file],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 1)

        file1 = SimpleUploadedFile(
            name='selfie1.jpg',
            content=str.encode('a fake image 1'),
            content_type='image/jpeg',
        )
        file2 = SimpleUploadedFile(
            name='selfie2.jpg',
            content=str.encode('a fake image 2'),
            content_type='image/jpeg',
        )
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'a selfie',
            'files': [file1, file2],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 3)

        retrieve_url = TWEET_RETRIEVE_API.format(response.data['id'])
        response = self.user1_client.get(retrieve_url)
        self.assertEqual(len(response.data['photo_urls']), 2)
        self.assertEqual('selfie1' in response.data['photo_urls'][0], True)
        self.assertEqual('selfie2' in response.data['photo_urls'][1], True)

        files = [
            SimpleUploadedFile(
                name=f'selfie{i}.jpg',
                content=str.encode(f'selfie{i}'),
                content_type='image/jpeg',
        )
            for i in range(10)
        ]
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'failed due to number of photos exceeded limit',
            'files': files,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(TweetPhoto.objects.count(), 3)

    def test_pagination(self):
        page_size = EndlessPagination.page_size

        for i in range(page_size * 2 - len(self.tweets1)):
            self.tweets1.append(self.create_tweet(self.user1, 'tweet{}'.format(i)))

        tweets = self.tweets1[::-1]

        response = self.user1_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], tweets[0].id)
        self.assertEqual(response.data['results'][1]['id'], tweets[1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], tweets[page_size - 1].id)

        response = self.user1_client.get(TWEET_LIST_API, {
            'created_at__lt': tweets[page_size - 1].created_at,
            'user_id': self.user1.id,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], tweets[page_size].id)
        self.assertEqual(response.data['results'][1]['id'], tweets[page_size + 1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], tweets[2 * page_size - 1].id)

        response = self.user1_client.get(TWEET_LIST_API, {
            'created_at__gt': tweets[0].created_at,
            'user_id': self.user1.id,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        new_tweet = self.create_tweet(self.user1, 'a new tweet comes in')

        response = self.user1_client.get(TWEET_LIST_API, {
            'created_at__gt': tweets[0].created_at,
            'user_id': self.user1.id,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_tweet.id)
