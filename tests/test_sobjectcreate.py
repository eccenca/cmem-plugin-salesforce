"""test sobjectcreate"""

import pytest
from simple_salesforce.exceptions import SalesforceAuthenticationFailed

from cmem_plugin_salesforce.workflow.operations import SobjectCreate


def test_invalid_credentials() -> None:
    """Test plugin execution"""
    with pytest.raises(SalesforceAuthenticationFailed):
        SobjectCreate(username="", password="", security_token="", salesforce_object="Lead")


def test_sobject_required() -> None:
    """Validate Required fields"""
    with pytest.raises(ValueError, match=r"Salesforce Object API Name is required."):
        SobjectCreate(username="", password="", security_token="", salesforce_object="")
