from django.contrib.auth.models import User
from django.contrib.auth import (
    login as django_login,
    logout as django_logout,
    authenticate as django_authenticate,
)
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.api.serializers import (
    UserSerializer,
    LoginSerializer,
    SignupSerializer,
    UserProfileSerializerForUpdate,
    UserSerializerWithProfile,
)
from accounts.models import UserProfile
from utils.permissions import IsObjectOwner


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializerWithProfile
    permission_classes = (permissions.IsAdminUser, )


    """
    api/uers/1
    api/uers/2
    """


class UserProfileViewSet(
    viewsets.GenericViewSet,
    viewsets.mixins.UpdateModelMixin,
):
    queryset = UserProfile
    permission_classes = (permissions.IsAuthenticated, IsObjectOwner, )
    serializer_class = UserProfileSerializerForUpdate


class AccountViewSet(viewsets.ViewSet):
    serializer_class = SignupSerializer #for testing

    @action(methods=["GET"], detail=False)
    def login_status(self, request):
        data = {
            'has_logged_in': request.user.is_authenticated,
            'ip': request.META['REMOTE_ADDR'],
        }
        if request.user.is_authenticated:
            data['user'] = UserSerializer(request.user).data
        return Response(data)

    @action(methods=["POST"], detail=False)
    def logout(self, request):
        django_logout(request)
        return Response({"success":True})

    @action(methods=["POST"], detail=False)
    def login(self, request):
        #get username and password from request
        serializer = LoginSerializer(data = request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Please check input",
                "errors": serializer.errors,
            }, status=400)

        #validation ok, login
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = django_authenticate(username = username, password = password)
        if not user or user.is_anonymous:
            return Response({
                "success": False,
                "message": "username and password does not match",
                "errors": serializer.errors,
            }, status=400)

        django_login(request, user)

        return Response({
            "success":True,
            "user": UserSerializer(user).data,
        })

    @action(methods=["POST"], detail=False)
    def signup(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Please check input",
                "errors": serializer.errors,
            }, status=400)

        user = serializer.save()
        django_login(request, user)

        return Response({
            "success":True,
            "user": UserSerializer(user).data,
        }, status=201)