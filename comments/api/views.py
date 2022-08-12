from comments.api.permissions import IsObjectOwner
from comments.api.serializers import CommentSerializerForCreate, CommentSerializer, CommentSerializerForUpdate
from comments.models import Comment
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response


class CommentViewSet(viewsets.GenericViewSet):
    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ["destroy", "update"]:
            return [IsAuthenticated(), IsObjectOwner()]
        return [AllowAny()]

    def list(self, request):

        comments = Comment.objects.all().order_by('-created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response({'comments': serializer.data})

    def create(self, request, *args, **kwargs):
        data = {
            'user_id': request.user.id,
            'tweet_id': request.data.get('tweet_id'),
            'content': request.data.get('content'),
        }

        serializer = CommentSerializerForCreate(
            data=data,
        )
        if not serializer.is_valid():
            return Response({
                "message": "Please check input",
                "errors": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        comment = serializer.save()
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        serializer = CommentSerializerForUpdate(
            instance = self.get_object(),
            data = request.data,
        )
        if not serializer.is_valid():
            return Response({
                "message": "Please check input",
                "errors": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        comment = serializer.save()
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        return Response({'success': True}, status=status.HTTP_200_OK)
