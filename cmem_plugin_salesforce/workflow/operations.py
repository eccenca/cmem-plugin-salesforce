"""Sales force CRUD operations module"""
import json
from typing import Sequence, Optional

from cmem_plugin_base.dataintegration.description import PluginParameter, Plugin
from cmem_plugin_base.dataintegration.entity import Entities
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.types import StringParameterType
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
            param_type=StringParameterType()
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
        self.username = username
        self.password = password
        self.security_token = security_token
        self.salesforce = Salesforce(username=self.username,
                                     password=self.password,
                                     security_token=self.security_token)
        self.salesforce_object = salesforce_object

    def get_connection(self) -> Salesforce:
        """Get salesforce connection object"""
        return self.salesforce

    def execute(self, inputs: Sequence[Entities]) -> Optional[Entities]:
        if len(inputs) == 0:
            self.log.info('No Entities found')
            return None
        for entities_collection in inputs:
            self.process(entities_collection)

        return None

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
                record[column] = ','.join(values[i])
                i += 1

            data.append(record)

        # TODO find an alternative to get SFType
        # pylint: disable=unnecessary-dunder-call
        bulk_object_type: SFBulkType = self.get_connection().bulk.__getattr__(
            self.salesforce_object
        )
        # pylint: enable=unnecessary-dunder-call
        self.log.info(f'Using __getattr__::{type(bulk_object_type)}')

        result = bulk_object_type.upsert(data=data, external_id_field='Id')
        self.log.info(json.dumps(result))
