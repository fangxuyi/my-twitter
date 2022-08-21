from inbox.api.serializers import NotificationSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class NotificationViewSet(
    viewsets.GenericViewSet,
    viewsets.mixins.ListModelMixin,
):
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated, )
    filterset_fields = ('unread', )

    def get_queryset(self):
        return self.request.user.notifications.all()

    @action(methods=["GET"], detail=False, url_path='unread-count')
    def unread_count(self, request, *args, **kwargs):
        # GET /api/notifications/unread_count/ by default. overrides to unread-count with url_path
        count = self.get_queryset().filter(unread=True).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)

    @action(methods=["POST"], detail=False, url_path='mark-all-as-read')
    def mark_all_as_read(self, request, *args, **kwargs):
        # GET /api/notifications/unread_count/ by default. overrides to unread-count with url_path
        updated_count = self.get_queryset().update(unread=False)
        return Response({'marked_count': updated_count}, status=status.HTTP_200_OK)

