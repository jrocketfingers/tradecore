import json

import pytest
from rest_framework import status
from rest_framework.reverse import reverse


# Could be split into two tests, but adds no significant value, at the cost of two integration tests.
@pytest.mark.django_db
@pytest.mark.integration
def test_post_creation(authenticated_client, post_dict, user, bogus_request):
    """
    Verify that the post can be created successfully, and that it's authored by the authenticated user.
    """
    response = authenticated_client.post(reverse('post-list'), data=post_dict)

    assert response.status_code == status.HTTP_201_CREATED

    user_url = reverse('user-detail', args=(user.pk,), request=bogus_request)

    post_json_response = json.loads(response.content)

    assert post_json_response['author'] == user_url

