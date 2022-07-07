import uuid

import pytest
from cmem_plugin_salesforce.workflow.operations import SobjectCreate
from simple_salesforce.exceptions import SalesforceAuthenticationFailed
from .utils import needs_sf, get_salesforce_config

from cmem_plugin_base.dataintegration.entity import (
    EntitySchema,
    EntityPath,
    Entity,
    Entities
)

def test_invalid_credentials():
    """Test plugin execution"""
    with pytest.raises(SalesforceAuthenticationFailed):
        SobjectCreate(username='', password='', security_token='', salesforce_object="Lead")


def test_sobject_required():
    """Validate Required fields"""
    with pytest.raises(ValueError, match='Salesforce Object API Name is required.'):
        SobjectCreate(username='', password='', security_token='', salesforce_object=None)

    with pytest.raises(ValueError, match='Salesforce Object API Name is required.'):
        SobjectCreate(username='', password='', security_token='', salesforce_object="")


@needs_sf
def test_create_lead():
    """Test create new lead record flow"""
    sf_config = get_salesforce_config()
    s_object_create = SobjectCreate(
        username=sf_config['username'],
        password=sf_config['password'],
        security_token=sf_config['securtiy_token'],
        salesforce_object="Lead")

    s_object_create.execute(get_lead_entities())


def get_lead_entities():
    """get entities object with lead columns"""
    projections = ['FirstName', "LastName"]
    entities = []
    paths = []
    entity_uri = f"urn:uuid:{str(uuid.uuid4())}"
    values = [[f'{str(uuid.uuid4())}'] for _ in projections]
    entities.append(
        Entity(
            uri=entity_uri,
            values=values
        )
    )
    paths = [EntityPath(path=projection) for projection in projections]

    schema = EntitySchema(
            type_uri="https://example.org/vocab/salesforce",
            paths=paths,
        )
    Entities(entities=entities, schema=schema)
