"""Sales force CRUD operations module"""

import time
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from cmem_plugin_base.dataintegration.context import ExecutionContext, ExecutionReport
from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.entity import (
    Entities,
    Entity,
    EntityPath,
    EntitySchema,
)
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from simple_salesforce import Salesforce

from cmem_plugin_salesforce import (
    LINKS,
    SECURITY_TOKEN_DESCRIPTION,
    USERNAME_DESCRIPTION,
)

if TYPE_CHECKING:
    from simple_salesforce.bulk import SFBulkType

PLUGIN_DOCUMENTATION = f"""
This task retrieves data from an incoming workflow task (such as a SPARQL query),
and sends bulk API requests to the Salesforce Object API, in order to
manipulate data in your organization's Salesforce account.

The working model is:

- Each entity from the input data is interpreted as a single Salesforce object of the
configured object type.
- Each path from the input entity is interpreted as a field from the Salesforce
data model (refer to  the {LINKS["OBJECT_REFERENCE"]}).
- The special path `id` is used to identify an object in Salesforce and switch
between update/creation mode, means:
  - If there is NO id path available, a new object is created.
  - If there IS an id path available, an update is done if the object exists.

Example:

- You want to create new Lead objects based on data from a Knowledge Graph.
- The {LINKS["LEAD_REFERENCE"]} lists the supported fields, e.g. `FirstName`,
  `LastName` and `Email`.
- Your input SPARQL task looks like this. Note that the variables need
  to match the field strings from the Salesforce data model:

```sparql
SELECT DISTINCT FirstName, LastName, Email ...
```

- You select `Lead` as the Object API Name of this task and you connect both task in
the workflow in order get the result of the SPARQL task as in input for this task.
- For each SPARQL result, a new Lead is created.
"""


@Plugin(
    label="Create/Update Salesforce Objects",
    description="Manipulate data in your organization's Salesforce account.",
    documentation=PLUGIN_DOCUMENTATION,
    parameters=[
        PluginParameter(
            name="username",
            label="Username",
            description=USERNAME_DESCRIPTION,
        ),
        PluginParameter(name="password", label="Password"),
        PluginParameter(
            name="security_token",
            label="Security Token",
            description=SECURITY_TOKEN_DESCRIPTION,
        ),
        PluginParameter(
            name="salesforce_object",
            label="Object API Name",
            description="""Salesforce Object API Name""",
        ),
    ],
)
class SobjectCreate(WorkflowPlugin):
    """Salesforce Create Record(s)"""

    def __init__(
        self, username: str, password: str, security_token: str, salesforce_object: str
    ) -> None:
        self.log.info("Salesforce Create Record(s)")

        if salesforce_object is None or salesforce_object == "":
            raise ValueError("Salesforce Object API Name is required.")
        self.salesforce_object = salesforce_object

        self.username = username
        self.password = password
        self.security_token = security_token
        self.salesforce = Salesforce(
            username=self.username,
            password=self.password,
            security_token=self.security_token,
        )

    def get_connection(self) -> Salesforce:
        """Get salesforce connection object"""
        return self.salesforce

    def execute(self, inputs: Sequence[Entities], context: ExecutionContext) -> Entities | None:
        """Execute create plugin flow"""
        summary: list[tuple[str, str]] = []
        if not inputs:
            self.log.info("No Entities found")
            return None
        results = []
        context.report.update(
            ExecutionReport(
                entity_count=0,
                operation="wait",
            )
        )
        for entities_collection in inputs:
            results.extend(self.process(entities_collection))
            context.report.update(
                ExecutionReport(
                    entity_count=len(results),
                    operation="wait",
                )
            )
        created, updated, failed, error_messages = self.get_summary_from_result(results)
        summary.append(("No. of entities created in Salesforce", f"{created}"))
        summary.append(("No. of entities updated in Salesforce", f"{updated}"))

        warnings = []
        if failed > 0:
            warnings.append(f"{failed} entities failed to create/update in Salesforce")

        if error_messages:
            warnings.append(f"Consolidated Errors: {error_messages}")

        context.report.update(
            ExecutionReport(
                entity_count=len(results),
                operation="read",
                summary=summary,
                warnings=warnings,
            )
        )
        return None

    def validate_columns(self, columns: Sequence[str]) -> None:
        """Validate the columns name against salesforce object"""
        # TODO(saipraneeth): find an alternative to get SFType  #noqa: TD003
        describe = self.get_connection().__getattr__(self.salesforce_object).describe()  # type: ignore[operator]

        object_fields = [field["name"] for field in describe["fields"]]
        columns_not_available = set(columns) - set(object_fields)
        if columns_not_available:
            raise ValueError(
                f"Columns {columns_not_available} are "
                f"not available in Salesforce Object {self.salesforce_object}"
            )

    def process(self, entities_collection: Entities):  # noqa: ANN201
        """Extract the data from entities and create in salesforce"""
        columns = [ep.path for ep in entities_collection.schema.paths]
        self.validate_columns(columns)
        data = []
        for entity in entities_collection.entities:
            values = entity.values
            record = {}
            for index, column in enumerate(columns):
                if column.lower() != "id" or values[index]:
                    record[column] = ",".join(values[index])

            data.append(record)

        self.log.info(f"Data : {data}")
        # TODO(saipraneeth): find an alternative to get SFType  #noqa: TD003
        bulk_object_type: SFBulkType = self.get_connection().bulk.__getattr__(  # type: ignore[assignment, union-attr]
            self.salesforce_object
        )
        result = bulk_object_type.upsert(data=data, external_id_field="Id")  # type: ignore[arg-type]

        current_timestamp = round(time.time()) * 1000
        for res in result:
            res["timestamp"] = current_timestamp

        return result

    def create_entities_from_result(self, result: list[dict[str, Any]]) -> Entities:
        """Create entities from result list"""
        self.log.info("Start of create_entities_from_result")
        entities = []
        for record in result:
            entity_uri = f"urn:uuid:{uuid.uuid4()!s}"
            values: list = [[f"{record[key]}"] for key in record]
            entities.append(Entity(uri=entity_uri, values=values))
        if entities:
            paths = [EntityPath(path=key) for key in result[0]]

        schema = EntitySchema(
            type_uri="https://vocab.eccenca.com/salesforce/result",
            paths=paths,
        )
        return Entities(entities=entities, schema=schema)

    def get_summary_from_result(self, result: list[dict[str, Any]]) -> tuple[int, int, int, str]:
        """Get summary from result list"""
        self.log.info("Start of get_summary_from_result")
        created: int = 0
        updated: int = 0
        error: int = 0
        error_messages: set = set()
        for record in result:
            if record["success"] and record["created"]:
                created += 1
            elif record["success"]:
                updated += 1
            else:
                error += 1

            for errors in record["errors"]:
                error_messages.add(f"{errors}")

        return created, updated, error, ",".join(error_messages)
