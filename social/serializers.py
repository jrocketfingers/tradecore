# pylint: disable=missing-docstring

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.reverse import reverse

from social.models import UserProfile, Post, Like


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password', 'user_profile',)
        read_only = ('password',)
        extra_kwargs = {'password': {'write_only': True}}


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class PostSerializer(serializers.HyperlinkedModelSerializer):
    likes = serializers.SerializerMethodField()
    like_detail = serializers.SerializerMethodField()
    like_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = '__all__'

    def get_likes(self, obj):
        return obj.likes.count()

    def get_like_detail(self, obj):
        request = self.context['request']
        try:
            like = obj.likes.get(user=request.user)
            return reverse('like-detail', args=[like.id], request=request)
        except Like.DoesNotExist:
            return None

    def get_like_url(self, obj):
        request = self.context['request']

        return reverse('post-like', args=[obj.id], request=request)


class LikeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'
        read_only = ('user', 'post',)

