"""
Social network construct models.
"""

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models

# The model names in this module should be entirelly clear.
# If not, consider renaming instead of elaborating using a docstring.
# pylint: disable=missing-docstring

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='user_profile', on_delete=models.CASCADE)
    enrichment_data = JSONField()


class Post(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    title = models.CharField(max_length=255)
    text = models.TextField()

    author = models.ForeignKey(User, related_name='posts')


class Like(models.Model):
    user = models.ForeignKey(User, related_name='likes')
    post = models.ForeignKey(Post, related_name='likes')

    class Meta:
        unique_together = (('user', 'post',),)

