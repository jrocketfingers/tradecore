# pylint: disable=missing-docstring

from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.reverse import reverse

from social.models import UserProfile, Post, Like


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'first_name', 'last_name', 'email', 'password', 'user_profile', 'posts',)
        read_only_fields = ('user_profile',)
        extra_kwargs = {'password': {'write_only': True}}

    # NOTE: Password hashing is done manually, since we need a rest endpoint for it. A third party library like Djoser
    #       could've been used, but it would introduce more complexity than necessary.
    #       It can be argued that we should send the password already hashed, but it's both less convinent to do it on
    #       all the clients, and the http transport on production software should already be secured by TLS.
    def prepare_password(self, validated_data):
        password = validated_data.pop('password')
        validated_data['password'] = make_password(password)

        return validated_data

    def create(self, validated_data):
        validated_data = self.prepare_password(validated_data)
        return super(UserSerializer, self).create(validated_data)

    def update(self, obj, validated_data):
        validated_data = self.prepare_password(validated_data)
        return super(UserSerializer, self).update(obj, validated_data)


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class PostSerializer(serializers.HyperlinkedModelSerializer):
    like_url = serializers.SerializerMethodField()
    like_action = serializers.SerializerMethodField()
    n_likes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = ('url', 'created_at', 'title', 'text', 'author', 'n_likes', 'like_action', 'like_url',)
        read_only_fields = ('author',)

    def create(self, validated_data):
        # Override any attempts at specifying the author out-of-context
        validated_data['author'] = self.context['request'].user
        return super(PostSerializer, self).create(validated_data)

    def update(self, obj, validated_data):
        # Override any attempts at specifying the author out-of-context
        validated_data['author'] = self.context['request'].user
        return super(PostSerializer, self).update(obj, validated_data)

    def get_like_url(self, obj):
        request = self.context['request']

        # Some of the checks were a bit rushed to get to the functional state
        # TODO: make the control flow more pleasant
        if not isinstance(request.user, AnonymousUser):
            try:
                like = obj.likes.get(user=request.user)
                return reverse('like-detail', args=[like.id], request=request)
            except Like.DoesNotExist:
                return None
        else:
            return None

    def get_like_action(self, obj):
        request = self.context['request']

        return reverse('post-like', args=[obj.id], request=request)


class LikeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'
        read_only = ('user', 'post',)

