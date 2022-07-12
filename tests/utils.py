"""Testing utilities."""
import os
from typing import Optional

import pytest

# check for cmem environment and skip if not present
from _pytest.mark import MarkDecorator
from cmem_plugin_base.dataintegration.context import ExecutionContext, ReportContext

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


class TestExecutionContext(ExecutionContext):
    """dummy plugin context that can be used in tests"""

    __test__ = False

    def __init__(self, project_id: str = "dummyProject",
                 report: Optional[ReportContext] = ReportContext()):
        self.project_id = project_id
        self.report = report
