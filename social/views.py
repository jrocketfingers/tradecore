from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from social import serializers
from social.models import UserProfile, Post, Like


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer

    def create(self, request, *args, **kwargs):
        # NOTE: The options for overriding the creation are either the `create`
        #       method, or the `perform_create` method.
        #       `perform_create` might've been more suitable if it the low API
        #       quotas for the demo were not an issue. Since we need to avoid
        #       spending the quotas each time the bot runs, we'll use a request
        #       parameter to denote bot account creations which would skip
        #       pinging the APIs and instead use fake data.
        serializer = self.get_serializer(data=request.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = serializers.UserProfileSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = serializers.PostSerializer

    # TODO: Remove upon setting default
    permission_classes = (IsAuthenticated,)
    authentication_class = (JSONWebTokenAuthentication,)

    @detail_route(methods=['post'])
    def like(self, request, pk=None):
        post = self.get_object()

        like, created = Like.objects.get_or_create(post=post, user=request.user)

        # We should notify about an already existing like
        if not created:
            return Response({'error': 'Like already placed.'}, status=status.HTTP_409_CONFLICT)

        serializer = serializers.LikeSerializer(like, context={'request': request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @detail_route(methods=['delete'])
    def unlike(self, request, pk=None):
        post = self.get_object()

        _, result = Like.objects.filter(post=post, user=request.user).delete()

        return Response(result)


class LikeViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.LikeSerializer

    def get_queryset(self):
        return self.request.user.likes.all()
