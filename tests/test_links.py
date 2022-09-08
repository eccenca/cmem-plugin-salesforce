"""Test the used documentation links."""
import requests as requests

from cmem_plugin_salesforce.workflow.soql_query import LINKS as SOQL_LINKS
from cmem_plugin_salesforce.workflow.operations import LINKS as SOBJECT_LINKS


def _valdate_link_list(links):
    for key, link in links.items():
        try:
            response = requests.get(link.url)
            assert response.status_code == 200, f"Documentation link not accessible: {link.url}"
        except Exception as error:
            assert error is None, f"Linked page not accessible {type(error)}: {link.url}"


def test_accessible_documentation_links():
    """This test fetches all used links to have response code 200."""
    _valdate_link_list(SOQL_LINKS)
    _valdate_link_list(SOBJECT_LINKS)
