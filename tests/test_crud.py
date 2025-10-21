"""Test sobject create plugin and soql plugin with inter dependent salesforce records"""

import uuid

import pytest
from cmem_plugin_base.dataintegration.entity import (
    Entities,
    Entity,
    EntityPath,
    EntitySchema,
)
from simple_salesforce import Salesforce

from cmem_plugin_salesforce.workflow.operations import SobjectCreate
from cmem_plugin_salesforce.workflow.soql_query import SoqlQuery

from .utils import TestExecutionContext, get_salesforce_config, needs_sf

SAMPLE_DATA = {
    "FirstName": f"{uuid.uuid4()!s}",
    "LastName": f"{uuid.uuid4()!s}",
    "Company": f"Plugin Test:{uuid.uuid4()!s}",
}


@pytest.fixture
def cleanup() -> None:
    """Clean the test records create by test run"""
    sf_config = get_salesforce_config()
    sf = Salesforce(
        username=sf_config["username"],
        password=sf_config["password"],
        security_token=sf_config["security_token"],
    )
    result = sf.query_all(f"SELECT Id from Lead where Company='{SAMPLE_DATA['Company']}'")
    if result["totalSize"] != 0:
        data = [{"Id": record["Id"]} for record in result["records"]]

        sf.bulk.Lead.delete(data, batch_size=10000, use_serial=True)


@needs_sf
@pytest.mark.dependency
def test_create_lead() -> None:
    """Test create new lead record flow"""
    sf_config = get_salesforce_config()
    s_object_create = SobjectCreate(
        username=sf_config["username"],
        password=sf_config["password"],
        security_token=sf_config["security_token"],
        salesforce_object="Lead",
    )
    entities = get_lead_entities()
    s_object_create.execute([entities], TestExecutionContext())


@pytest.mark.dependency(depends=["test_create_lead"])
def test_soql() -> None:
    sf_config = get_salesforce_config()
    query = (
        f"SELECT {','.join(list(SAMPLE_DATA))} FROM Lead WHERE Company = '{SAMPLE_DATA['Company']}'"
    )
    soql_query = SoqlQuery(
        username=sf_config["username"],
        password=sf_config["password"],
        security_token=sf_config["security_token"],
        soql_query=query,
    )

    entities = soql_query.execute(None, TestExecutionContext)
    result = get_dict_from_entity(entities.entities[0], entities.schema)
    assert result == SAMPLE_DATA


def get_dict_from_entity(entity: Entity, schema: EntitySchema) -> dict:
    result = {}
    for i in range(len(entity.values)):
        result[schema.paths[i].path] = ",".join(entity.values[i])
    return result


def get_lead_entities() -> Entities:
    """Get entities object with lead columns"""
    projections = list(SAMPLE_DATA)
    entities = []
    entity_uri = f"urn:uuid:{uuid.uuid4()!s}"
    values = [[SAMPLE_DATA[_]] for _ in projections]
    entities.append(Entity(uri=entity_uri, values=values))
    paths = [EntityPath(path=projection) for projection in projections]

    schema = EntitySchema(
        type_uri="https://example.org/vocab/salesforce",
        paths=paths,
    )
    return Entities(entities=entities, schema=schema)
