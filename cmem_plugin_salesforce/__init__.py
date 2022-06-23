"""Salesforce Integration Plugin"""
import json
import io
import pyparsing

from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.parameter.dataset import DatasetParameterType
from cmem_plugin_base.dataintegration.parameter.multiline import (
    MultilineStringParameterType,
)
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.utils import write_to_dataset
from simple_salesforce import Salesforce, SalesforceMalformedRequest
from python_soql_parser import parse


def validate_soql(soql_query: str) -> bool:
    """ Validate SOQL """
    try:
        parse(soql_query=soql_query)
        return True
    except pyparsing.ParseException:
        return False


@Plugin(
    label="Salesforce",
    description="The salesforce plugin is intended as a 2way bridge between "
                "salesforce and a Knowledge Graph",
    documentation="""
The values required to connect salesforce client

- `dataset`: Dataset to which the data should be written.
- `username`: Username of the Salesforce Account.
- `password`: Password of the Salesforce Account.
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
            name="soql_query",
            label="SOQL Query",
            description="""The query text of the GraphQL Query you want to execute.
            GraphQL is a query language for APIs and a runtime for
            fulfilling those queries with your existing data.
            Learn more on GraphQL [here](https://graphql.org/).
            }""",
            param_type=MultilineStringParameterType(),
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
    """Salesforce Integration Plugin"""

    # pylint: disable=R0913
    def __init__(
            self,
            username: str,
            password: str,
            security_token: str,
            soql_query: str,
            dataset: str = "",
    ) -> None:
        self.dataset = dataset
        self.username = username
        self.password = password
        self.security_token = security_token
        if not validate_soql(soql_query):
            raise ValueError("SOQL Query is not valid")

        self.soql_query = soql_query

    def execute(self, inputs=()):
        salesforce = Salesforce(username=self.username,
                                password=self.password,
                                security_token=self.security_token)

        auth = salesforce.headers.get('Authorization')
        if len(auth) > 0:
            try:
                result = salesforce.query(self.soql_query)
                write_to_dataset(self.dataset,
                                 io.StringIO(json.dumps(result, indent=2)))
            except SalesforceMalformedRequest:
                self.log.info("Malformed Request")
