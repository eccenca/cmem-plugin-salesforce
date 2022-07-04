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
