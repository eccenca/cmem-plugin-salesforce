"""Salesforce Integration Plugin"""
import io
import json
import uuid
from collections import OrderedDict

from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.entity import (
    EntitySchema,
    EntityPath,
    Entity,
    Entities
)
from cmem_plugin_base.dataintegration.parameter.dataset import DatasetParameterType
from cmem_plugin_base.dataintegration.parameter.multiline import (
    MultilineStringParameterType,
)
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.types import BoolParameterType
from cmem_plugin_base.dataintegration.utils import write_to_dataset
from python_soql_parser import parse
from simple_salesforce import (
    Salesforce,
    SalesforceLogin
)


def validate_soql(soql_query: str):
    """ Validate SOQL """
    parse(soql_query=soql_query)


def validate_credentials(username: str, password: str, security_token: str):
    """ Validate Salesforce login credentials"""
    SalesforceLogin(username=username,
                    password=password,
                    security_token=security_token)


def get_projections(record: OrderedDict) -> list[str]:
    """get keys from dict"""
    projections = list(record)
    # Remove metadata keys
    projections.remove('attributes')
    return projections


@Plugin(
    label="Salesforce SOQL Query",
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
            description="""SOQL QUERY""",
            param_type=MultilineStringParameterType()
        ),
        PluginParameter(
            name="dataset",
            label="Dataset",
            description="Dateset name to save the response from Salesforce Plugin",
            param_type=DatasetParameterType(dataset_type="json"),
            advanced=True,
            default_value=''
        ),
        PluginParameter(
            name="parse_soql",
            label="Parse SOQL",
            description="Parse SOQL Query before execution",
            param_type=BoolParameterType(),
            advanced=True,
            default_value=True
        ),
    ]
)
class SoqlQuery(WorkflowPlugin):
    """Salesforce Integration Plugin"""

    # pylint: disable-msg=too-many-arguments
    def __init__(
            self,
            username: str,
            password: str,
            security_token: str,
            soql_query: str,
            dataset: str = "",
            parse_soql: bool = False
    ) -> None:
        validate_credentials(username, password, security_token)

        self.dataset = dataset
        self.username = username
        self.password = password
        self.security_token = security_token
        if parse_soql:
            validate_soql(soql_query)

        self.soql_query = soql_query

    def execute(self, inputs=()) -> Entities:
        self.log.info("Start Salesforce Plugin")
        salesforce = Salesforce(username=self.username,
                                password=self.password,
                                security_token=self.security_token)

        result = salesforce.query_all(self.soql_query)
        records = result.pop('records')
        projections = get_projections(records[0])
        self.log.info(f"Config length: {len(self.config.get())}")
        entities = []
        for record in records:
            entity_uri = f"urn:uuid:{str(uuid.uuid4())}"
            values = [[f'{record.pop(projection)}'] for projection in projections]
            entities.append(
                Entity(
                    uri=entity_uri,
                    values=values
                )
            )

        paths = [EntityPath(path=projection) for projection in projections]

        # TODO rename type uri
        schema = EntitySchema(
            type_uri="https://example.org/vocab/salesforce",
            paths=paths,
        )

        self.log.info(f"Happy to serve "
                      f"{result.pop('totalSize')} salesforce data.")
        if len(self.dataset) > 0:
            write_to_dataset(self.dataset,
                             io.StringIO(json.dumps(result, indent=2)))

        return Entities(entities=entities, schema=schema)
