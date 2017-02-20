import pytest
from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.test import APIClient

from social.models import User
from social.serializers import UserSerializer


@pytest.mark.django_db
@pytest.mark.integration
def test_register_as_a_bot(mock, client, clearbit, user_dict):
    """
    In case registration is triggered by the bot, api quotas should not be used.
    """
    mock.patch('social.views.User')
    mock.patch('social.views.UserProfile')

    # register a user with an additional bot query param
    response = client.post('/api/v1/user/?bot=true', user_dict)

    assert response.content == 'abc'

    # check that the enrichment hasn't been called
    assert not clearbit.called, "Bot should not be calling the API."


@pytest.mark.django_db
@pytest.mark.integration
def test_register_as_a_human(mock, client, clearbit, user_dict):
    """
    In case registration is called by a human, api should be used as expected.
    """
    mock.patch('social.views.User')
    mock.patch('social.views.UserProfile')

    # register a user without the bot query param
    client.post('/api/v1/user/', user_dict)

    # check that the enrichment api _has_ been called
    assert clearbit.called, "Regular registration should call the API."


@pytest.mark.django_db
@pytest.mark.integration
def test_hash_password_on_register(client, user_dict):
    """
    Check if the password is actually hashed upon registration
    """
    client.post('/api/v1/user/?bot=true', user_dict)

    user = User.objects.get(username=user_dict['username'])

    assert check_password(user_dict['password'], user.password), "Password is not properly set at registration."


@pytest.mark.django_db
@pytest.mark.integration
def test_password_change(client, user):
    # pylint: disable=missing-docstring
    new_password = 'test'

    response = client.patch(f'/api/v1/user/{user.pk}/', {'password': new_password})
    assert response.status_code == status.HTTP_200_OK, "User PATCH response is not 200."

    user = User.objects.get(pk=user.pk)
    assert check_password(new_password, user.password)


@pytest.mark.unit
def test_serializer_password_prepare():
    # pylint: disable=missing-docstring
    password = 'test'

    serializer = UserSerializer()
    validated_data = serializer.prepare_password({'password': password})

    assert check_password(password, validated_data['password'])
