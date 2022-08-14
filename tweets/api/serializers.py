from rest_framework import serializers
from tweets.models import Tweet
from accounts.api.serializers import UserSerializerForTweet
from comments.api.serializers import CommentSerializer


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet()

    class Meta:
        model = Tweet
        fields = ('id', 'user', 'created_at', 'content')

class TweetSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)

    class Meta:
        model = Tweet
        fields = ('content', )

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        return tweet

class TweetSerializerWithComments(TweetSerializer):
    comments = CommentSerializer(source="comment_set", many =True)

    #with SerializerMethodField
    #comments = serializers.SerializerMethodField()
    #def get_comments(self, object):
    #    return CommentSerializer(object.comment_set.all(), many =True).data

    class Meta:
        model = Tweet
        fields = ("id", "user", "created_at", "content", "comments")
