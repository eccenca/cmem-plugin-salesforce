"""Salesforce Integration Plugin"""

import io
import json
import uuid
from collections import OrderedDict
from collections.abc import Sequence

from cmem_plugin_base.dataintegration.context import ExecutionContext
from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.entity import (
    Entities,
    Entity,
    EntityPath,
    EntitySchema,
)
from cmem_plugin_base.dataintegration.parameter.dataset import DatasetParameterType
from cmem_plugin_base.dataintegration.parameter.multiline import (
    MultilineStringParameterType,
)
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.utils import write_to_dataset
from simple_salesforce import Salesforce, SalesforceLogin

from cmem_plugin_salesforce import (
    LINKS,
    SECURITY_TOKEN_DESCRIPTION,
    USERNAME_DESCRIPTION,
)

EXAMPLE_FIELDS_QUERY = "SELECT FIELDS(STANDARD) FROM Lead"
EXAMPLE_QUERY = "SELECT Contact.Firstname, Contact.Lastname FROM Contact"

PLUGIN_DOCUMENTATION = f"""
This task executes a custom Salesforce Object Query (SOQL)
and returns sets of tabular data from your organization's Salesforce account.

> Use the Salesforce Object Query Language (SOQL) to search your organization's
> Salesforce data for specific information. SOQL is similar to the SELECT statement in
> the widely used Structured Query Language (SQL) but is designed specifically for
> Salesforce data.
-- <cite>{LINKS["SOQL_INTRO"]}</cite>

SOQL uses the SELECT statement combined with filtering statements to return sets of
data, which can optionally be ordered. For a complete description of the syntax, see
{LINKS["SOQL_SYNTAX"]}.

This task ignores any entities it receives; the query comes only from the SOQL Query
parameter. A query that matches no records fails with an error rather than returning
an empty result.

Examples:

Retrieve all standard fields from all Lead resources.
```
{EXAMPLE_FIELDS_QUERY}
```
Retrieve first name and last name of all Contact resources.
```
{EXAMPLE_QUERY}
```

Please refer to the {LINKS["OBJECT_REFERENCE"]} of the Salesforce Platform data
model in order to get an overview of the available objects and fields.
"""  # noqa: S608

SOQL_DESCRIPTION = f"""
The query text of your SOQL query.

SOQL uses the SELECT statement combined with filtering statements to return sets
of data, which can optionally be ordered. For a complete description of the syntax,
see {LINKS["SOQL_SYNTAX"]}.
"""


def validate_credentials(username: str, password: str, security_token: str) -> None:
    """Validate Salesforce login credentials"""
    SalesforceLogin(username=username, password=password, security_token=security_token)


def get_projections(record: OrderedDict) -> list[str]:
    """Get keys from dict"""
    projections = list(record)
    # Remove metadata keys
    projections.remove("attributes")
    return projections


@Plugin(
    label="SOQL query (Salesforce)",
    plugin_id="cmem_plugin_salesforce-SoqlQuery",
    description="Executes a custom Salesforce Object Query (SOQL) to return"
    " sets of data your organization's Salesforce account.",
    documentation=PLUGIN_DOCUMENTATION,
    parameters=[
        PluginParameter(
            name="username",
            label="Username",
            description=USERNAME_DESCRIPTION,
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
            description="Besides the direct output of the fetched entities, write the"
            " complete raw query response - including Salesforce's internal metadata"
            " for each record - to a JSON dataset (mostly for debugging purposes).",
            param_type=DatasetParameterType(dataset_type="json"),
            advanced=True,
            default_value="",
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
    ) -> None:
        validate_credentials(username, password, security_token)

        self.dataset = dataset
        self.username = username
        self.password = password
        self.security_token = security_token
        self.soql_query = soql_query

    def execute(self, inputs: Sequence[Entities], context: ExecutionContext) -> Entities:
        """Execute SOQL query plugin flow"""
        self.log.info("Start Salesforce Plugin")
        _ = inputs
        salesforce = Salesforce(
            username=self.username,
            password=self.password,
            security_token=self.security_token,
        )

        result = salesforce.query_all(self.soql_query)
        # Snapshot the full response before records/totalSize are popped below and
        # before the entity-building loop pops every field out of each record dict -
        # otherwise the dataset write below would only ever see {"done": true}.
        dataset_content = json.dumps(result, indent=2, ensure_ascii=False)
        records = result.pop("records")
        projections = get_projections(records[0])
        self.log.info(f"Config length: {len(self.config.get())}")
        entities = []
        for record in records:
            entity_uri = f"urn:uuid:{uuid.uuid4()!s}"
            values = [[f"{record.pop(projection)}"] for projection in projections]
            entities.append(Entity(uri=entity_uri, values=values))

        paths = [EntityPath(path=projection) for projection in projections]
        # TODO(saipraneeth): rename type uri  # noqa: TD003
        schema = EntitySchema(
            type_uri="https://example.org/vocab/salesforce",
            paths=paths,
        )

        self.log.info(f"Happy to serve {result.pop('totalSize')} salesforce data.")
        if self.dataset:
            write_to_dataset(
                self.dataset, io.BytesIO(dataset_content.encode("utf-8")), context=context.user
            )

        return Entities(entities=entities, schema=schema)
