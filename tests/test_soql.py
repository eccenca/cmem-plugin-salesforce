"""Plugin tests."""
import pytest
from cmem_plugin_salesforce.workflow.operations import SobjectCreate
from simple_salesforce.exceptions import SalesforceAuthenticationFailed


def test_invalid_credentials():
    """Test plugin execution"""
    with pytest.raises(SalesforceAuthenticationFailed):
        SobjectCreate(username='', password='', security_token='', salesforce_object="Lead")
