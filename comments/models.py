from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import pre_delete, post_save
from comments.listeners import decr_comments_count, incr_comments_count
from likes.models import Like
from tweets.models import Tweet
from utils.memcached_helper import MemcachedHelper

class Comment(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
    )
    tweet = models.ForeignKey(
        Tweet,
        on_delete=models.SET_NULL,
        null=True,
    )
    content = models.TextField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        index_together = (
            ('tweet','created_at'),
        )

    def __str__(self):
        return f"{self.created_at} - {self.user} says {self.content} at tweet {self.tweet_id}"

    @property
    def like_set(self):
        #tweet.like_set() to get all likes for this tweet
        return Like.objects.filter(
            content_type = ContentType.objects.get_for_model(Comment),
            object_id=self.id,
        ).order_by('-created_at')

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.user_id)

pre_delete.connect(decr_comments_count, sender=Comment)
post_save.connect(incr_comments_count, sender=Comment)