from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from newsfeeds.models import NewsFeed
from newsfeeds.api.serializers import NewsFeedSerializer
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def get_queryset(self):
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        queryset = NewsFeed.objects.filter(user=self.request.user)
        newsfeeds = self.paginate_queryset(queryset)
        serializer = NewsFeedSerializer(newsfeeds, context={'request':request},many=True)
        return self.get_paginated_response(serializer.data)