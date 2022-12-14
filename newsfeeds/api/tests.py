from django.conf import settings

from friendships.api.tests import FRIENDSHIP_FOLLOW_URL
from friendships.models import Friendship
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from testing.testcases import TestCase
from rest_framework.test import APIClient
from tweets.api.tests import TWEET_CREATE_API
from utils.paginations import EndlessPagination

NEWSFEED_LIST_API = '/api/newsfeeds/'

class NewsFeedApiTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user("user1")
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user("user2")
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(self.user2)


    def test_list(self):
        response = self.anonymous_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 403)

        response = self.user1_client.post(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 405)

        response = self.user1_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)

        self.user1_client.post(TWEET_CREATE_API, {'content': "Hello World"})
        response = self.user1_client.get(NEWSFEED_LIST_API)
        self.assertEqual(len(response.data['results']), 1)

        self.user1_client.post(FRIENDSHIP_FOLLOW_URL.format(self.user2.id))
        response = self.user2_client.post(TWEET_CREATE_API, {'content': "Hello World"})
        posted_tweet_id = response.data["id"]
        response = self.user1_client.get(NEWSFEED_LIST_API)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['tweet']['id'], posted_tweet_id)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        followed_user = self.create_user('followed')
        newsfeeds = []
        for i in range(page_size * 2):
            tweet = self.create_tweet(followed_user)
            newsfeed = self.create_newsfeed(self.user1, tweet=tweet)
            newsfeeds.append(newsfeed)

        newsfeeds = newsfeeds[::-1]

        response = self.user1_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[0].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], newsfeeds[page_size - 1].id)

        response = self.user1_client.get(NEWSFEED_LIST_API, {
            'created_at__lt': newsfeeds[page_size - 1].created_at,
            'user_id': self.user1.id,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[page_size].id)
        self.assertEqual(response.data['results'][1]['id'], newsfeeds[page_size + 1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], newsfeeds[2 * page_size - 1].id)

        response = self.user1_client.get(NEWSFEED_LIST_API, {
            'created_at__gt': newsfeeds[0].created_at,
            'user_id': self.user1.id,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        tweet = self.create_tweet(followed_user)
        newsfeed = self.create_newsfeed(self.user1, tweet=tweet)

        response = self.user1_client.get(NEWSFEED_LIST_API, {
            'created_at__gt': newsfeeds[0].created_at,
            'user_id': self.user1.id,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], newsfeed.id)

    def test_user_cache(self):
        profile = self.user2.profile
        profile.nickname = 'user2'
        profile.save()

        self.assertEqual(self.user1.username, 'user1')
        self.create_newsfeed(self.user2, self.create_tweet(self.user1))
        self.create_newsfeed(self.user2, self.create_tweet(self.user2))

        response = self.user2_client.get(NEWSFEED_LIST_API)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'user2')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'user2')
        self.assertEqual(results[1]['tweet']['user']['username'], 'user1')

        self.user1.username = 'user1_update'
        self.user1.save()
        profile.nickname = 'user2_update'
        profile.save()

        response = self.user2_client.get(NEWSFEED_LIST_API)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'user2')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'user2_update')
        self.assertEqual(results[1]['tweet']['user']['username'], 'user1_update')

    def test_tweet_cache(self):
        tweet = self.create_tweet(self.user1, 'content1')
        self.create_newsfeed(self.user2, tweet)
        response = self.user2_client.get(NEWSFEED_LIST_API)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'user1')
        self.assertEqual(results[0]['tweet']['content'], 'content1')

        self.user1.username = 'user1_update'
        self.user1.save()
        response = self.user2_client.get(NEWSFEED_LIST_API)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'user1_update')

        tweet.content = 'content2'
        tweet.save()
        response = self.user2_client.get(NEWSFEED_LIST_API)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['content'], 'content2')

    def _paginate_to_get_newsfeeds(self, client):
        response = client.get(NEWSFEED_LIST_API)
        results = response.data['results']
        while response.data['has_next_page']:
            created_at__lt = response.data['results'][-1]['created_at']
            response = client.get(NEWSFEED_LIST_API, {'created_at__lt': created_at__lt})
            results.extend(response.data['results'])
        return results

    def test_redis_list_limit(self):
        list_limit = settings.REDIS_LIST_LENGTH_LIMIT
        page_size = EndlessPagination.page_size
        users = [self.create_user('user{}'.format(i)) for i in range(5, 10)]
        newsfeeds = []
        for i in range(list_limit + page_size):
            tweet = self.create_tweet(user=users[i % 5], content = 'feed{}'.format(i))
            feed = self.create_newsfeed(self.user1, tweet)
            newsfeeds.append(feed)
        newsfeeds = newsfeeds[::-1]

        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user1.id)
        self.assertEqual(len(cached_newsfeeds), list_limit)
        queryset = NewsFeed.objects.filter(user=self.user1)
        self.assertEqual(queryset.count(), list_limit + page_size)

        results = self._paginate_to_get_newsfeeds(self.user1_client)
        self.assertEqual(len(results), list_limit + page_size)
        for i in range(list_limit + page_size):
            self.assertEqual(newsfeeds[i].id, results[i]["id"])

        self.create_friendship(self.user1, self.user2)
        new_tweet = self.create_tweet(self.user2, 'a new tweet')
        NewsFeedService.fanout_to_followers(new_tweet)

        def _test_newsfeeds_after_new_feed_pushed():
            results = self._paginate_to_get_newsfeeds(self.user1_client)
            self.assertEqual(len(results), list_limit + page_size + 1)
            self.assertEqual(results[0]['tweet']['id'], new_tweet.id)
            for i in range(list_limit + page_size):
                self.assertEqual(newsfeeds[i].id, results[i+1]['id'])

        _test_newsfeeds_after_new_feed_pushed()

        # cache expired
        self.clear_cache()
        _test_newsfeeds_after_new_feed_pushed()
