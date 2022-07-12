"""Sales force CRUD operations module"""
import time
import uuid
from typing import Sequence, Optional, Any, Tuple

from cmem_plugin_base.dataintegration.context import ExecutionContext, ExecutionReport
from cmem_plugin_base.dataintegration.description import PluginParameter, Plugin
from cmem_plugin_base.dataintegration.entity import (
    Entities, Entity, EntityPath, EntitySchema
)
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from simple_salesforce import Salesforce
from simple_salesforce.bulk import SFBulkType


@Plugin(
    label="Salesforce Create Record(s)",
    description="The plugin is used to create records in salesforce",
    documentation="""
The values required to connect salesforce client

- `username`: Username of the Salesforce Account.
- `password`: Password of the Salesforce Account.
- 'security_token': Security Token of the Salesforce Account.
- 'object' : Salesforce Object API Name
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
            name="salesforce_object",
            label="Object API Name",
            description="""Salesforce Object API Name""",
        )
    ]
)
class SobjectCreate(WorkflowPlugin):
    """Salesforce Create Record(s)"""

    def __init__(
            self,
            username: str,
            password: str,
            security_token: str,
            salesforce_object: str
    ) -> None:
        self.log.info("Salesforce Create Record(s)")

        if salesforce_object is None or salesforce_object == '':
            raise ValueError('Salesforce Object API Name is required.')
        self.salesforce_object = salesforce_object

        self.username = username
        self.password = password
        self.security_token = security_token
        self.salesforce = Salesforce(username=self.username,
                                     password=self.password,
                                     security_token=self.security_token)

    def get_connection(self) -> Salesforce:
        """Get salesforce connection object"""
        return self.salesforce

    def execute(self, inputs: Sequence[Entities],
                context: ExecutionContext) -> Optional[Entities]:
        summary: list[Tuple[str, str]] = []
        if len(inputs) == 0:
            self.log.info('No Entities found')
            return None
        results = []
        context.report.update(
            ExecutionReport(
                entity_count=0,
                operation='wait',
            )
        )
        for entities_collection in inputs:
            results.extend(
                 self.process(entities_collection)
            )
            context.report.update(
                ExecutionReport(
                    entity_count=len(results),
                    operation='wait',
                )
            )
        created, updated, failed, error_messages = self.get_summary_from_result(results)
        summary.append(('No. of entities created in Salesforce', f'{created}'))
        summary.append(('No. of entities updated in Salesforce', f'{updated}'))

        warnings = []
        if failed > 0:
            warnings.append(f'{failed} entities failed to create/update in Salesforce')

        if len(error_messages) > 0:
            warnings.append(f'Consolidated Errors: {error_messages}')

        context.report.update(
            ExecutionReport(
                entity_count=len(results),
                operation='read',
                summary=summary,
                warnings=warnings
            )
        )
        return None
        # return self.create_entities_from_result(results)

    def validate_columns(self, columns: Sequence[str]):
        """Validate the columns name against salesforce object"""
        # TODO find an alternative to get SFType
        # pylint: disable=unnecessary-dunder-call
        describe = self.get_connection().__getattr__(self.salesforce_object).describe()
        # pylint: enable=unnecessary-dunder-call

        object_fields = [field['name'] for field in describe['fields']]
        columns_not_available = set(columns)-set(object_fields)
        if len(columns_not_available):
            raise ValueError(
                f'Columns {columns_not_available} are '
                f'not available in Salesforce Object {self.salesforce_object}'
            )

    def process(self, entities_collection: Entities):
        """Extract the data from entities and create in salesforce"""
        columns = [ep.path for ep in entities_collection.schema.paths]
        self.validate_columns(columns)
        data = []
        for entity in entities_collection.entities:
            values = entity.values
            record = {}
            i = 0
            for column in columns:
                if column.lower() != 'id' or len(values[i]) != 0:
                    record[column] = ','.join(values[i])
                i += 1

            data.append(record)

        self.log.info(f'Data : {data}')
        # TODO find an alternative to get SFType
        # pylint: disable=unnecessary-dunder-call
        bulk_object_type: SFBulkType = self.get_connection().bulk.__getattr__(
            self.salesforce_object
        )
        # pylint: enable=unnecessary-dunder-call
        result = bulk_object_type.upsert(data=data, external_id_field='Id')

        current_timestamp = round(time.time()) * 1000
        for res in result:
            res['timestamp'] = current_timestamp

        return result

    def create_entities_from_result(self, result: list[dict[str, Any]]):
        """Create entities from result list"""
        self.log.info('Start of create_entities_from_result')
        entities = []
        for record in result:
            entity_uri = f"urn:uuid:{str(uuid.uuid4())}"
            values: list = [[f'{record[key]}'] for key in record]
            entities.append(
                Entity(uri=entity_uri, values=values)
            )
        if len(entities) != 0:
            paths = [EntityPath(path=key) for key in result[0]]

        schema = EntitySchema(
            type_uri="https://vocab.eccenca.com/salesforce/result",
            paths=paths,
        )
        return Entities(entities=entities, schema=schema)

    def get_summary_from_result(self, result: list[dict[str, Any]]):
        """Get summary from result list"""
        self.log.info('Start of get_summary_from_result')
        created: int = 0
        updated: int = 0
        error: int = 0
        error_messages: set = set()
        for record in result:
            if record['success'] and record['created']:
                created += 1
            elif record['success']:
                updated += 1
            else:
                error += 1

            for errors in record['errors']:
                error_messages.add(f'{errors}')

        return created, updated, error, ",".join(error_messages)
