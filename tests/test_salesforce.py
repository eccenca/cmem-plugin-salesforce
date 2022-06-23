"""Plugin tests."""
import pytest
from cmem_plugin_salesforce import SalesforcePlugin


def test_execution():
    """Test plugin execution"""
    SalesforcePlugin(username='', password='', security_token='', dataset='', soql_query='SELECT Id, Name FROM Contact')



