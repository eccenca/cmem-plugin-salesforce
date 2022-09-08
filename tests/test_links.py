"""Test the used documentation links."""
import requests as requests

from cmem_plugin_salesforce.workflow.soql_query import LINKS


def test_accessible_documentation_links():
    """This test fetches all used links to have response code 200."""
    for key, link in LINKS.items():
        try:
            response = requests.get(link.url)
            assert response.status_code == 200, f"Documentation link not accessible: {link.url}"
        except Exception as error:
            assert error is None, f"Linked page not accessible {type(error)}: {link.url}"
