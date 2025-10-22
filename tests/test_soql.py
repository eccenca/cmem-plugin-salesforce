"""Plugin tests."""

import pytest
from simple_salesforce.exceptions import SalesforceAuthenticationFailed

from cmem_plugin_salesforce.workflow.soql_query import SoqlQuery


def test_invalid_credentials() -> None:
    """Test plugin execution"""
    with pytest.raises(SalesforceAuthenticationFailed):
        SoqlQuery(
            username="",
            password="",
            security_token="",
            dataset="",
            soql_query="SELECT Id, Name FROM Contact",
        )
