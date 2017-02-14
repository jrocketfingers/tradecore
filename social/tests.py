from rest_framework.test import APIClient
from utils import model_to_dict

def test_user_registration_using_the_bot(mock):
    enrichment_find_mock = mock.patch('social.views.clearbit.Enrichment.find', autospec=True)

    client = APIClient()
    
    # register a user with an additional bot query param

    # check that the enrichment hasn't been called
    enrichment_find_mock.assert_not_called()
