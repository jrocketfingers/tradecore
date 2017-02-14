from dateutil.relativedelta import relativedelta

import factory
import factory.fuzzy
from django.contrib.auth.models import User
from django.utils import timezone

from social.models import UserProfile, Post


class UserProfileFactory(factory.DjangoModelFactory):
    enrichment_data = {}

    class Meta:
        model = UserProfile


class UserFactory(factory.DjangoModelFactory):
    password = factory.Faker("password")
    username = factory.Faker("user_name")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    is_staff = False
    is_active = True
    date_joined = factory.fuzzy.FuzzyDateTime(end_dt=timezone.now(), start_dt=(timezone.now() - relativedelta(years=1)))
    user_profile = factory.RelatedFactory(UserProfileFactory, 'user')

    class Meta:
        model = User


class PostFactory(factory.DjangoModelFactory):
    title = factory.Faker("sentence")
    text = factory.Faker("text")

    author = factory.SubFactory(UserFactory)

    class Meta:
        model = Post

