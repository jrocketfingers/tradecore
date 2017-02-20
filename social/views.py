import clearbit
from django.contrib.auth.models import User, AnonymousUser
from django.db import transaction
from django.db.models import Count
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from social import serializers
from social.models import UserProfile, Post, Like


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer

    def create(self, request, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        # create is a view method and should run before perform_create, or we're looking at a flawed design

        # is it the bot calling?
        self.bot = self.request.query_params.get('bot', False)

        # NOTE: Consider using py3 sugar? super()
        return super(UserViewSet, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        with transaction.atomic():
            user = serializer.save()

            enrichment_data = None

            if not self.bot:
                # NOTE: Could be moved to social.apps and used as a module import to make sure it's initialized?
                clearbit.key = settings.CLEARBIT_API_KEY
                enrichment_data = clearbit.Enrichment.find(email=user.email, stream=True)

            UserProfile.objects.create(user=user, enrichment_data=enrichment_data)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = serializers.UserProfileSerializer


class PostViewSet(viewsets.ModelViewSet):
    """
    Unlisted routes (as per [#2062](https://github.com/tomchristie/django-rest-framework/issues/2062)):

    - `/api/v1/post/newsfeed/` - posts from users other than the logged in user
    - `/api/v1/post/personal/` - your own posts
    - `/api/v1/post/<id>/like/` - like the post
    - delete request to `like_url` - unlike the post

    `like_url` - represents the logged in user's detail view of the like, hence the nulls on posts the user has not
                 liked
    """
    serializer_class = serializers.PostSerializer
    filter_backends = (OrderingFilter,)
    ordering_fields = ('n_likes', 'created_at',)

    authentication_class = (JSONWebTokenAuthentication,)

    def get_queryset(self):
        queryset = Post.objects.annotate(n_likes=Count('likes')).all()

        n_likes = self.request.query_params.get('likes', None)

        if n_likes is not None:
            queryset = queryset.filter(n_likes=n_likes)

        return queryset

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

    def render_list_response(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def personal(self, request):
        queryset = self.filter_queryset(Post.objects.filter(author=request.user))

        return self.render_list_response(queryset)

    @list_route(methods=['get'])
    def newsfeed(self, request):
        queryset = self.filter_queryset(Post.objects.exclude(author=request.user))

        return self.render_list_response(queryset)


class LikeViewSet(viewsets.ModelViewSet):
    """
    Shows likes from the current user.

    TODO: setup object level permissions
    """
    serializer_class = serializers.LikeSerializer

    def get_queryset(self):
        try:
            return self.request.user.likes.all()
        except AttributeError:
            if not isinstance(self.request.user, AnonymousUser):
                raise
            return None

