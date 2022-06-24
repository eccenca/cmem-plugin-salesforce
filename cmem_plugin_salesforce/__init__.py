"""Salesforce Integration Plugin"""
import json
import uuid
import io

import pyparsing

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

    def execute(self, inputs=()) -> Entities:
        salesforce = Salesforce(username=self.username,
                                password=self.password,
                                security_token=self.security_token)

        if len(salesforce.headers.get('Authorization')) > 0:
            try:
                projections = parse(self.soql_query)['fields']
                result = salesforce.query(self.soql_query)
                records = result.pop('records')

                self.log.info("Start Salesforce Plugin")
                self.log.info(f"Config length: {len(self.config.get())}")

                entities = []
                for record in records:
                    entity_uri = f"urn:uuid:{str(uuid.uuid4())}"
                    values = []
                    for projection in projections:
                        values.append([record.pop(f'{projection}')])
                    entities.append(
                        Entity(
                            uri=entity_uri,
                            values=values
                        )
                    )

                paths = []
                for projection in projections:
                    path_uri = f"{projection}"
                    paths.append(
                        EntityPath(
                            path=path_uri
                        )
                    )

                schema = EntitySchema(
                    type_uri="https://example.org/vocab/salesforce",
                    paths=paths,
                )

                self.log.info(f"Happy to serve "
                              f"{result.pop('totalSize')} salesforce data.")
                write_to_dataset(self.dataset,
                                 io.StringIO(json.dumps(result, indent=2)))

                return Entities(entities=entities, schema=schema)

            except SalesforceMalformedRequest:
                self.log.info("Malformed Request")
                return Entities(entities=[Entity(uri='', values=[])],
                                schema=EntitySchema(type_uri='', paths=[]))
        else:
            return Entities(entities=[Entity(uri='', values=[])],
                            schema=EntitySchema(type_uri='', paths=[]))
