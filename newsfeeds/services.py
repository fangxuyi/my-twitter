from newsfeeds.tasks import fanout_newsfeeds_main_task
from newsfeeds.models import NewsFeed
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_helper import RedisHelper

class NewsFeedService(object):

    @classmethod
    def fanout_to_followers(cls, tweet):

        fanout_newsfeeds_main_task.delay(tweet.id, tweet.user_id)
        # followers = FriendshipService.get_followers(tweet.user)
        # newsfeeds = [
        #     NewsFeed(user=follower, tweet=tweet)
        #     for follower in followers
        # ]
        # newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        # NewsFeed.objects.bulk_create(newsfeeds)
        #
        # #bulk_create does not trigger post_save
        # for newsfeed in newsfeeds:
        #     cls.push_newsfeed_to_cache(newsfeed)

    @classmethod
    def get_cached_newsfeeds(cls, user_id):
        queryset = NewsFeed.objects.filter(user_id=user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, queryset)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        queryset = NewsFeed.objects.filter(user_id=newsfeed.user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)
        return RedisHelper.push_objects(key, newsfeed, queryset)
