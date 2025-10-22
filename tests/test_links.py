"""Test the used documentation links."""

from http import HTTPStatus

import requests

from cmem_plugin_salesforce import LINKS, MarkdownLink


def _validate_link_list(links: dict[str, MarkdownLink]) -> None:
    for link in links.values():
        response = requests.get(link.url, timeout=10)
        response.raise_for_status()  # will raise HTTPError if not OK
        assert response.status_code == HTTPStatus.OK, (
            f"Documentation link not accessible: {link.url}"
        )


def test_accessible_documentation_links() -> None:
    """Test fetches all used links to have response code 200."""
    _validate_link_list(LINKS)
