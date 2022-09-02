"""Testing utilities."""
import os
from typing import Optional

import pytest
import requests

from cmem.cmempy.api import get_token

from cmem_plugin_base.dataintegration.context import (
    PluginContext,
    UserContext,
    TaskContext,
    ExecutionContext,
    ReportContext,
)

# check for cmem environment and skip if not present
needs_cmem = pytest.mark.skipif(
    os.environ.get("CMEM_BASE_URI", "") == "", reason="Needs CMEM configuration"
)
needs_sf = pytest.mark.skipif(
    "SF_USERNAME" not in os.environ,
    "SF_PASSWORD" not in os.environ,
    "SF_SECURITY_TOKEN" not in os.environ,
    reason="Needs Salesforce login configuration",
)


def get_salesforce_config():
    """To get the salesforce login configuration from environment variables"""
    return {
        "username": os.environ.get("SF_USERNAME", ""),
        "password": os.environ.get("SF_PASSWORD", ""),
        "security_token": os.environ.get("SF_SECURITY_TOKEN", ""),
    }


class TestUserContext(UserContext):
    """dummy user context that can be used in tests"""

    __test__ = False

    def token(self) -> str:
        return get_token()["access_token"]


class TestPluginContext(PluginContext):
    """dummy plugin context that can be used in tests"""

    __test__ = False

    def __init__(
        self,
        project_id: str = "dummyProject",
        user: Optional[UserContext] = TestUserContext(),
    ):
        self.project_id = project_id
        self.user = user


class TestTaskContext(TaskContext):
    """dummy Task context that can be used in tests"""

    __test__ = False

    def __init__(self, project_id: str = "dummyProject"):
        self.project_id = lambda: project_id


class TestExecutionContext(ExecutionContext):
    """dummy execution context that can be used in tests"""

    __test__ = False

    def __init__(
        self,
        project_id: str = "dummyProject",
        user: Optional[UserContext] = TestUserContext(),
    ):
        self.report = ReportContext()
        self.task = TestTaskContext(project_id=project_id)
        self.user = user
