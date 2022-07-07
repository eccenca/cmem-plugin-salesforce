"""Testing utilities."""
import os

import pytest

# check for cmem environment and skip if not present
from _pytest.mark import MarkDecorator

needs_cmem: MarkDecorator = pytest.mark.skipif(
    "CMEM_BASE_URI" not in os.environ, reason="Needs CMEM configuration"
)

needs_sf: MarkDecorator = pytest.mark.skipif(
    "SF_USERNAME" not in os.environ,
    "SF_PASSWORD" not in os.environ,
    "SF_SECURITY_TOKEN" not in os.environ,
    reason="Needs Salesforce login configuration"
)


def get_salesforce_config():
    """To get the salesforce login configuration from environment variables"""
    return {
        "username":  os.environ["SF_USERNAME"] if "SF_USERNAME" in os.environ else '',
        "password": os.environ["SF_PASSWORD"] if "SF_PASSWORD" in os.environ else '',
        "security_token": os.environ["SF_SECURITY_TOKEN"] if "SF_SECURITY_TOKEN" in os.environ else ''
    }

