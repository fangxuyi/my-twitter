from accounts.api.serializers import UserSerializerWithProfile
from comments.api.serializers import CommentSerializer
from likes.api.serializer import LikeSerializer
from likes.services import LikeService
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from tweets.constants import TWEET_PHOTOS_UPLOAD_LIMIT
from tweets.models import Tweet
from tweets.services import TweetService


#denormalization makes one number available at multiple places
#increases efficiency as avoids N+1 query
#however, brings inconsistency issues
#source of truth is still the old N+1 query
class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerWithProfile()
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()
    photo_urls = serializers.SerializerMethodField()


    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comments_count',
            'likes_count',
            'has_liked',
            'photo_urls',
        )

    def get_has_liked(self, obj):
        return LikeService.has_liked(self.context['request'].user, obj)

    def get_comments_count(self, obj):
        #return obj.comments_count
        return obj.comment_set.count()

    # N+1 query
    def get_likes_count(self, obj):
        #return obj.likes_count
        return obj.like_set.count()

    def get_photo_urls(self, obj):
        photo_urls = []
        for photo in obj.tweetphoto_set.all().order_by('order'):
            photo_urls.append(photo.file.url)
        return photo_urls

class TweetSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)
    files = serializers.ListField(
        child = serializers.FileField(),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Tweet
        fields = ('content', 'files')

    def validate(self, data):
        if len(data.get('files', [])) > TWEET_PHOTOS_UPLOAD_LIMIT:
            raise ValidationError({
                'message': f'You can upload {TWEET_PHOTOS_UPLOAD_LIMIT} photos at most'
            })
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        if validated_data.get('files'):
            TweetService.create_photos_from_files(
                tweet,
                validated_data['files'],
            )
        return tweet

class TweetSerializerForDetail(TweetSerializer):
    comments = CommentSerializer(source="comment_set", many =True)
    likes = LikeSerializer(source='like_set', many=True)

    #with SerializerMethodField
    #comments = serializers.SerializerMethodField()
    #def get_comments(self, object):
    #    return CommentSerializer(object.comment_set.all(), many =True).data

    class Meta:
        model = Tweet
        fields = ("id",
                  "user",
                  "created_at",
                  "content",
                  "comments",
                  'comments_count',
                  "likes",
                  'likes_count',
                  'has_liked',
                  'photo_urls',
                  )
