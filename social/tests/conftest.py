"""
Testing fixtures for the social app.
"""

import factory
import pytest
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework_jwt.settings import api_settings

from social.factories import UserFactory, PostFactory


@pytest.fixture
def client():
    """
    Con
    """
    return APIClient()


@pytest.fixture
def authenticated_client(token):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'JWT {token}')

    return client


@pytest.fixture
def user():
    """
    Returns a new user, persisted to the database.
    """
    return UserFactory()


@pytest.fixture
def user_dict():
    """
    Returns a dictionary that corresponds to a new user.
    """
    return factory.build(dict, user_profile=None, FACTORY_CLASS=UserFactory)


@pytest.fixture
def post_dict():
    """
    Returns a dictionary that corresponds to a new user.
    """
    # NOTE: Author should be specified on the endpoint and determined by the token.
    #       The regular factory will still return a full blown post.
    post_data = factory.build(dict, author=None, FACTORY_CLASS=PostFactory)
    post_data.pop('author')

    return post_data


@pytest.fixture
def clearbit(mock):
    mock.patch('social.views.clearbit.key')
    enrichment_find_mock = mock.patch('social.views.clearbit.Enrichment.find')
    enrichment_find_mock.return_value = {}

    # NOTE: has to be a yield fixture, since mock is undone by the end of the function
    yield enrichment_find_mock


@pytest.fixture
def token(user):
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)

    return token


@pytest.fixture
def token_headers(token):
    return {'Authorization': f'JWT {token}'}


@pytest.fixture
def bogus_request():
    """
    Used to get any request whatsoever, since it's the least fragile way to retrieve the hostname for a request.
    Rest framework serializer relies on request object being able to get it's hostname for fully qualifed urls.
    """
    factory = APIRequestFactory()
    return factory.get('/')
