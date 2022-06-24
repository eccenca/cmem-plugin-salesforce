"""Plugin tests."""
import pytest
from cmem_plugin_salesforce.workflow.soql_query import SoqlQuery


def test_execution():
    """Test plugin execution"""
    SoqlQuery(username='', password='', security_token='', dataset='', soql_query='SELECT Id, Name FROM Contact')



