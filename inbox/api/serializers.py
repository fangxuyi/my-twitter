from notifications.models import Notification
from rest_framework import serializers


class NotificationSerializer(serializers.ModelSerializer):
    actor_content_type = serializers.SerializerMethodField()

    def get_actor_content_type(self, obj):
        return obj.actor_content_type.name

    class Meta:
        model = Notification
        fields = (
            'id',
            'actor_content_type',
            'actor_object_id',
            'verb',
            'action_object_content_type',
            'action_object_object_id',
            'target_content_type',
            'target_object_id',
            'timestamp',
            'unread',
        )

class NotificationSerializerForUpdate(serializers.ModelSerializer):
    unread = serializers.BooleanField()

    class Meta:
        model = Notification
        fields = ('unread', )

    def update(self, instance, validated_data):
        instance.unread = validated_data['unread']
        instance.save()
        return instance