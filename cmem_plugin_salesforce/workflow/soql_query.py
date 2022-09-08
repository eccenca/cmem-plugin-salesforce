"""Salesforce Integration Plugin"""
import io
import json
import uuid
from collections import OrderedDict
from typing import Sequence

from cmem_plugin_base.dataintegration.context import ExecutionContext
from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.entity import (
    EntitySchema,
    EntityPath,
    Entity,
    Entities,
)
from cmem_plugin_base.dataintegration.parameter.dataset import DatasetParameterType
from cmem_plugin_base.dataintegration.parameter.multiline import (
    MultilineStringParameterType,
)
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.types import BoolParameterType
from cmem_plugin_base.dataintegration.utils import write_to_dataset
from python_soql_parser import parse
from simple_salesforce import Salesforce, SalesforceLogin

from cmem_plugin_salesforce.helper import MarkdownLink

LINKS = {
    "SOQL_INTRO": MarkdownLink(
        "https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/"
        "soql_sosl/sforce_api_calls_soql.htm",
        "developer.salesforce.com"
    ),
    "SOQL_SYNTAX": MarkdownLink(
        "https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/"
        "soql_sosl/sforce_api_calls_soql_select.htm",
        "Salesforce SOQL SELECT Syntax"
    ),
    "OBJECT_REFERENCE": MarkdownLink(
        "https://developer.salesforce.com/docs/atlas.en-us.238.0."
        "object_reference.meta/object_reference/sforce_api_objects_list.htm",
        "Salesforce Standard Objects list"
    ),
    "DEV_CONSOLE": MarkdownLink(
        "https://help.salesforce.com/s/articleView?id=sf.code_dev_console.htm&type=5",
        "Salesforce Developer Console"
    ),
    "TOKEN_DOCU": MarkdownLink(
        "https://help.salesforce.com/"
        "s/articleView?id=sf.user_security_token.htm&type=5",
        "Salesforce Reset Token Documentation"
    )
}

EXAMPLE_QUERY = "SELECT FIELDS(STANDARD) FROM Lead"  # nosec

PLUGIN_DESCRIPTION = f"""
This task executes a custom Salesforce Object Query (SOQL)
and returns sets of tabular data from your organization’s Salesforce account.

> Use the Salesforce Object Query Language (SOQL) to search your organization’s
> Salesforce data for specific information. SOQL is similar to the SELECT statement in
> the widely used Structured Query Language (SQL) but is designed specifically for
> Salesforce data.
-- <cite>{LINKS["SOQL_INTRO"]}</cite>

SOQL uses the SELECT statement combined with filtering statements to return sets of
data, which can optionally be ordered. For a complete description of the syntax, see
{LINKS["SOQL_SYNTAX"]}.

Example: Retrieve all standard fields from all Lead resources.

```
{EXAMPLE_QUERY}
```

Please refer to the {LINKS["OBJECT_REFERENCE"]} of the Salesforce Platform data
model in order to get an overview of the available objects and fields.
"""

PARSE_SOQL_DESCRIPTION = f"""
Parse query text for validation.

To avoid mistakes, the plugin tries to validate the given query text before sending it
to Salesforce. Turn off this feature, in case you are encountering false validation
errors. You can always validate your query in the {LINKS["DEV_CONSOLE"]}.
"""

SECURITY_TOKEN_DESCRIPTION = f"""
In addition to your standard account credentials, you need to provide a security
token to access your data.

Refer to the {LINKS["TOKEN_DOCU"]} to learn how to retrieve or reset your token.
"""

SOQL_DESCRIPTION = f"""
The query text of your SOQL query.

SOQL uses the SELECT statement combined with filtering statements to return sets
of data, which can optionally be ordered. For a complete description of the syntax,
see {LINKS["SOQL_SYNTAX"]}.
"""


def validate_soql(soql_query: str):
    """Validate SOQL"""
    parse(soql_query=soql_query)


def validate_credentials(username: str, password: str, security_token: str):
    """Validate Salesforce login credentials"""
    SalesforceLogin(username=username, password=password, security_token=security_token)


def get_projections(record: OrderedDict) -> list[str]:
    """get keys from dict"""
    projections = list(record)
    # Remove metadata keys
    projections.remove("attributes")
    return projections


@Plugin(
    label="SOQL query (Salesforce)",
    plugin_id="cmem_plugin_salesforce-SoqlQuery",
    description="Executes a custom Salesforce Object Query (SOQL) to return"
                " sets of data your organization’s Salesforce account.",
    documentation=PLUGIN_DESCRIPTION,
    parameters=[
        PluginParameter(
            name="username",
            label="Username",
            description="Username of the Salesforce Account. This is typically your"
                        " eMail Address.",
        ),
        PluginParameter(
            name="password",
            label="Password",
        ),
        PluginParameter(
            name="security_token",
            label="Security Token",
            description=SECURITY_TOKEN_DESCRIPTION,
        ),
        PluginParameter(
            name="soql_query",
            label="SOQL Query",
            description=SOQL_DESCRIPTION,
            param_type=MultilineStringParameterType(),
        ),
        PluginParameter(
            name="dataset",
            label="Dataset",
            description="In addition to have direct output of the fetched entities of"
                        " your SOQL query, you can directly write the response to a"
                        " JSON dataset (mostly for debugging purpose).",
            param_type=DatasetParameterType(dataset_type="json"),
            advanced=True,
            default_value="",
        ),
        PluginParameter(
            name="parse_soql",
            label="Parse SOQL Query",
            description=PARSE_SOQL_DESCRIPTION,
            param_type=BoolParameterType(),
            advanced=True,
            default_value=True,
        ),
    ],
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
        parse_soql: bool = False,
    ) -> None:
        validate_credentials(username, password, security_token)

        self.dataset = dataset
        self.username = username
        self.password = password
        self.security_token = security_token
        if parse_soql:
            validate_soql(soql_query)

        self.soql_query = soql_query

    def execute(
        self, inputs: Sequence[Entities], context: ExecutionContext
    ) -> Entities:
        self.log.info("Start Salesforce Plugin")
        salesforce = Salesforce(
            username=self.username,
            password=self.password,
            security_token=self.security_token,
        )

        result = salesforce.query_all(self.soql_query)
        records = result.pop("records")
        projections = get_projections(records[0])
        self.log.info(f"Config length: {len(self.config.get())}")
        entities = []
        for record in records:
            entity_uri = f"urn:uuid:{str(uuid.uuid4())}"
            values = [[f"{record.pop(projection)}"] for projection in projections]
            entities.append(Entity(uri=entity_uri, values=values))

        paths = [EntityPath(path=projection) for projection in projections]

        # TODO rename type uri
        schema = EntitySchema(
            type_uri="https://example.org/vocab/salesforce",
            paths=paths,
        )

        self.log.info(f"Happy to serve " f"{result.pop('totalSize')} salesforce data.")
        if self.dataset:
            write_to_dataset(self.dataset, io.StringIO(json.dumps(result, indent=2)))

        return Entities(entities=entities, schema=schema)
