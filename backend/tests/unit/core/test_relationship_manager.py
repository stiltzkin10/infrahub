import pytest
from neo4j import AsyncSession

from infrahub.core import registry
from infrahub.core.branch import Branch
from infrahub.core.node import Node
from infrahub.core.relationship import RelationshipManager
from infrahub.core.utils import get_paths_between_nodes
from infrahub_client.timestamp import Timestamp


async def test_one_init_no_input_no_rel(session: AsyncSession, person_jack_main: Node, branch: Branch):
    person_schema = registry.get_schema(name="Person")
    rel_schema = person_schema.get_relationship("primary_tag")

    relm = await RelationshipManager.init(
        session=session, schema=rel_schema, branch=branch, at=Timestamp(), node=person_jack_main, name="primary_tag"
    )

    # shouldn't be able to iterate over it since it's a "one" relationship
    with pytest.raises(TypeError):
        iter(relm)

    assert not await relm.get_peer(session=session)


@pytest.fixture
async def person_jack_primary_tag_main(session: AsyncSession, person_tag_schema, tag_blue_main: Node) -> Node:
    obj = await Node.init(session=session, schema="Person")
    await obj.new(session=session, firstname="Jake", lastname="Russell", primary_tag=tag_blue_main)
    await obj.save(session=session)
    return obj


async def test_one_init_no_input_existing_rel(
    session: AsyncSession, tag_blue_main: Node, person_jack_primary_tag_main: Node, branch: Branch
):
    person_schema = registry.get_schema(name="Person")
    rel_schema = person_schema.get_relationship("primary_tag")

    relm = await RelationshipManager.init(
        session=session,
        schema=rel_schema,
        branch=branch,
        at=Timestamp(),
        node=person_jack_primary_tag_main,
        name="primary_tag",
    )

    peer = await relm.get_peer(session=session)
    assert peer.id == tag_blue_main.id


async def test_many_init_no_input_no_rel(session: AsyncSession, person_jack_main: Node, branch: Branch):
    person_schema = registry.get_schema(name="Person")
    rel_schema = person_schema.get_relationship("tags")

    relm = await RelationshipManager.init(
        session=session, schema=rel_schema, branch=branch, at=Timestamp(), node=person_jack_main, name="tags"
    )

    # shouldn't be able to query the peer since it's many type relationship
    with pytest.raises(TypeError):
        await relm.get_peer(session=session)

    assert not len(await relm.get(session=session))


async def test_many_init_no_input_existing_rel(session: AsyncSession, person_jack_tags_main: Node, branch: Branch):
    person_schema = registry.get_schema(name="Person")
    rel_schema = person_schema.get_relationship("tags")

    relm = await RelationshipManager.init(
        session=session, schema=rel_schema, branch=branch, at=Timestamp(), node=person_jack_tags_main, name="tags"
    )

    assert len(await relm.get(session=session)) == 2


async def test_one_init_input_obj(session: AsyncSession, tag_blue_main: Node, person_jack_main: Node, branch: Branch):
    person_schema = registry.get_schema(name="Person")
    rel_schema = person_schema.get_relationship("primary_tag")

    relm = await RelationshipManager.init(
        session=session,
        schema=rel_schema,
        branch=branch,
        at=Timestamp(),
        node=person_jack_main,
        name="primary_tag",
        data=tag_blue_main,
    )

    peer = await relm.get_peer(session=session)
    assert peer.id == tag_blue_main.id


async def test_one_save_input_obj(session: AsyncSession, tag_blue_main: Node, person_jack_main: Node, branch: Branch):
    person_schema = registry.get_schema(name="Person")
    rel_schema = person_schema.get_relationship("primary_tag")

    # We should have only 1 paths between t1 and p1 via the branch
    paths = await get_paths_between_nodes(
        session=session, source_id=tag_blue_main.db_id, destination_id=person_jack_main.db_id, max_length=2
    )
    assert len(paths) == 1

    relm = await RelationshipManager.init(
        session=session,
        schema=rel_schema,
        branch=branch,
        at=Timestamp(),
        node=person_jack_main,
        name="primary_tag",
        data=tag_blue_main,
    )
    await relm.save(session=session)

    # We should have 2 paths between t1 and p1
    # First for the relationship, Second via the branch
    paths = await get_paths_between_nodes(
        session=session, source_id=tag_blue_main.db_id, destination_id=person_jack_main.db_id, max_length=2
    )
    assert len(paths) == 2


async def test_one_udpate(
    session: AsyncSession, tag_blue_main: Node, person_jack_primary_tag_main: Node, branch: Branch
):
    person_schema = registry.get_schema(name="Person")
    rel_schema = person_schema.get_relationship("primary_tag")

    # We should have only 1 paths between t1 and p1 via the branch
    paths = await get_paths_between_nodes(
        session=session, source_id=tag_blue_main.db_id, destination_id=person_jack_primary_tag_main.db_id, max_length=2
    )
    assert len(paths) == 2

    relm = await RelationshipManager.init(
        session=session,
        schema=rel_schema,
        branch=branch,
        at=Timestamp(),
        node=person_jack_primary_tag_main,
        name="primary_tag",
        data=tag_blue_main,
    )
    await relm.save(session=session)

    # We should have 2 paths between t1 and p1
    # First for the relationship, Second via the branch
    paths = await get_paths_between_nodes(
        session=session, source_id=tag_blue_main.db_id, destination_id=person_jack_primary_tag_main.db_id, max_length=2
    )
    assert len(paths) == 2


async def test_many_init_input_obj(
    session: AsyncSession, tag_blue_main: Node, tag_red_main: Node, person_jack_main: Node, branch: Branch
):
    person_schema = registry.get_schema(name="Person")
    rel_schema = person_schema.get_relationship("tags")

    relm = await RelationshipManager.init(
        session=session,
        schema=rel_schema,
        branch=branch,
        at=Timestamp(),
        node=person_jack_main,
        name="tags",
        data=[tag_blue_main, tag_red_main],
    )

    assert len(list(relm)) == 2


async def test_many_save_input_obj(
    session: AsyncSession, tag_blue_main: Node, tag_red_main: Node, person_jack_main: Node, branch: Branch
):
    person_schema = registry.get_schema(name="Person")
    rel_schema = person_schema.get_relationship("tags")

    # We should have only 1 paths between t1 and p1 via the branch
    paths = await get_paths_between_nodes(
        session=session, source_id=tag_blue_main.db_id, destination_id=person_jack_main.db_id, max_length=2
    )
    assert len(paths) == 1

    paths = await get_paths_between_nodes(
        session=session, source_id=tag_red_main.db_id, destination_id=person_jack_main.db_id, max_length=2
    )
    assert len(paths) == 1

    relm = await RelationshipManager.init(
        session=session,
        schema=rel_schema,
        branch=branch,
        at=Timestamp(),
        node=person_jack_main,
        name="tags",
        data=[tag_blue_main, tag_red_main],
    )
    await relm.save(session=session)

    paths = await get_paths_between_nodes(
        session=session, source_id=tag_blue_main.db_id, destination_id=person_jack_main.db_id, max_length=2
    )
    assert len(paths) == 2

    paths = await get_paths_between_nodes(
        session=session, source_id=tag_red_main.db_id, destination_id=person_jack_main.db_id, max_length=2
    )
    assert len(paths) == 2


async def test_many_update(
    session: AsyncSession, tag_blue_main: Node, tag_red_main: Node, person_jack_main: Node, branch: Branch
):
    person_schema = registry.get_schema(name="Person")
    rel_schema = person_schema.get_relationship("tags")

    relm = await RelationshipManager.init(
        session=session, schema=rel_schema, branch=branch, at=Timestamp(), node=person_jack_main, name="tags"
    )
    await relm.save(session=session)

    # We should have only 1 paths between t1 and p1 via the branch
    paths = await get_paths_between_nodes(
        session=session, source_id=tag_blue_main.db_id, destination_id=person_jack_main.db_id, max_length=2
    )
    assert len(paths) == 1

    paths = await get_paths_between_nodes(
        session=session, source_id=tag_red_main.db_id, destination_id=person_jack_main.db_id, max_length=2
    )
    assert len(paths) == 1

    await relm.update(session=session, data=tag_blue_main)
    await relm.save(session=session)

    paths = await get_paths_between_nodes(
        session=session, source_id=tag_blue_main.db_id, destination_id=person_jack_main.db_id, max_length=2
    )
    assert len(paths) == 2

    paths = await get_paths_between_nodes(
        session=session, source_id=tag_red_main.db_id, destination_id=person_jack_main.db_id, max_length=2
    )
    assert len(paths) == 1

    await relm.update(session=session, data=[tag_blue_main, tag_red_main])
    await relm.save(session=session)

    paths = await get_paths_between_nodes(
        session=session, source_id=tag_blue_main.db_id, destination_id=person_jack_main.db_id, max_length=2
    )
    assert len(paths) == 2

    paths = await get_paths_between_nodes(
        session=session, source_id=tag_red_main.db_id, destination_id=person_jack_main.db_id, max_length=2
    )
    assert len(paths) == 2
