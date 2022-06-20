"""Salesforce Integration Plugin"""

import json
import io

from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.parameter.dataset import DatasetParameterType
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.utils import write_to_dataset
from simple_salesforce import Salesforce


@Plugin(
    label="Salesforce",
    description="The salesforce plugin is intended as a 2way bridge between "
                "salesforce and a Knowledge Graph",
    documentation="""
The values required to connect salesforce client

- `dataset`: Dataset to which the data should be written.
- 'username': Username of the Salesforce Account.
- 'password': Password of the Salesforce Account.
- 'security_token': Security Token of the Salesforce Account.
""",
    parameters=[
        PluginParameter(
            name="username",
            label="Username",
            description="Username of the Salesforce Account.",
        ),
        PluginParameter(
            name="password",
            label="Password",
            description="Password of the Salesforce Account.",
        ),
        PluginParameter(
            name="security_token",
            label="Security Token",
            description="Security Token of the Salesforce Account.",
        ),
        PluginParameter(
            name="dataset",
            label="Dataset",
            description="Dateset name to save the response from Salesforce Plugin",
            param_type=DatasetParameterType(dataset_type="json")
        ),
    ]
)
class SalesforcePlugin(WorkflowPlugin):
    """Example Workflow Plugin: Random Values"""

    def __init__(
            self,
            username: str,
            password: str,
            security_token: str,
            dataset: str = "",
    ) -> None:
        self.dataset = dataset
        self.username = username
        self.password = password
        self.security_token = security_token

    def execute(self, inputs=()):
        salesforce = Salesforce(username=self.username,
                                password=self.password,
                                security_token=self.security_token)

        auth = salesforce.headers.get('Authorization')
        if len(auth) > 0:
            result = salesforce.query("SELECT Id, Name FROM Contact")
            write_to_dataset(self.dataset,
                             io.StringIO(json.dumps(result, indent=2)))
