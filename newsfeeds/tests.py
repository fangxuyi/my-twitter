from newsfeeds.services import NewsFeedService
from testing.testcases import TestCase
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_client import RedisClient


class NewsFeedServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.user1 = self.create_user('user1')
        self.user2 = self.create_user('user2')

    def test_get_user_newsfeeds(self):
        newsfeeds_ids = []
        for i in range(3):
            tweet = self.create_tweet(self.user1)
            newsfeed = self.create_newsfeed(self.user2, tweet)
            newsfeeds_ids.append(newsfeed.id)
        newsfeeds_ids = newsfeeds_ids[::-1]

        #cache miss
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user2.id)
        self.assertEqual([t.id for t in newsfeeds], newsfeeds_ids)

        #cache hit
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user2.id)
        self.assertEqual([t.id for t in newsfeeds], newsfeeds_ids)

        #cache updated
        new_tweet = self.create_tweet(self.user1, "new tweet")
        newsfeed = self.create_newsfeed(self.user2, new_tweet)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.user2.id)
        newsfeeds_ids.insert(0, newsfeed.id)
        self.assertEqual([t.id for t in newsfeeds], newsfeeds_ids)

    def test_create_new_tweet_before_get_cached_tweets(self):
        feed1 = self.create_newsfeed(self.user1, self.create_tweet(self.user1))

        RedisClient.clear()
        conn = RedisClient.get_connection()

        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.user1.id)
        self.assertEqual(conn.exists(key), False)
        feed2 = self.create_newsfeed(self.user1, self.create_tweet(self.user1))
        self.assertEqual(conn.exists(key), True)

        feeds = NewsFeedService.get_cached_newsfeeds(self.user1.id)
        self.assertEqual([t.id for t in feeds], [feed2.id, feed1.id])
