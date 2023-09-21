import pytest
from graphql import graphql

from infrahub.core import registry
from infrahub.core.branch import Branch
from infrahub.core.initialization import create_branch
from infrahub.core.node import Node
from infrahub.graphql import generate_graphql_schema


@pytest.fixture
async def repos_and_checks_in_main(session, register_core_models_schema):
    repo01 = await Node.init(session=session, schema="CoreRepository")
    await repo01.new(session=session, name="repo01", location="git@github.com:user/repo01.git")
    await repo01.save(session=session)

    repo02 = await Node.init(session=session, schema="CoreRepository")
    await repo02.new(session=session, name="repo02", location="git@github.com:user/repo02.git")
    await repo02.save(session=session)

    query01 = await Node.init(session=session, schema="CoreGraphQLQuery")
    await query01.new(session=session, name="my_query", query="query { check { id } }")
    await query01.save(session=session)

    checkdef01 = await Node.init(session=session, schema="CoreCheckDefinition")
    await checkdef01.new(
        session=session,
        name="check01",
        query=query01,
        repository=repo01,
        file_path="check01.py",
        class_name="Check01",
        rebase=True,
    )
    await checkdef01.save(session=session)

    checkdef02 = await Node.init(session=session, schema="CoreCheckDefinition")
    await checkdef02.new(
        session=session,
        name="check02",
        query=query01,
        repository=repo02,
        file_path="check02.py",
        class_name="Check02",
        rebase=True,
    )
    await checkdef02.save(session=session)


async def test_branch_create(db, session, default_branch: Branch, car_person_schema, register_core_models_schema):
    schema = await generate_graphql_schema(branch=default_branch, session=session, include_subscription=False)

    query = """
    mutation {
        BranchCreate(data: { name: "branch2", is_data_only: true }) {
            ok
            object {
                id
                name
                description
                is_data_only
                is_default
                branched_from
            }
        }
    }
    """
    result = await graphql(
        schema,
        source=query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )

    assert result.errors is None
    assert result.data["BranchCreate"]["ok"] is True
    assert len(result.data["BranchCreate"]["object"]["id"]) == 36  # lenght of an UUID
    assert result.data["BranchCreate"]["object"]["name"] == "branch2"
    assert result.data["BranchCreate"]["object"]["description"] == ""
    assert result.data["BranchCreate"]["object"]["is_data_only"] is True
    assert result.data["BranchCreate"]["object"]["is_default"] is False
    assert result.data["BranchCreate"]["object"]["branched_from"] is not None

    branch2 = await Branch.get_by_name(session=session, name="branch2")
    branch2_schema = registry.schema.get_schema_branch(name=branch2.name)

    assert branch2
    assert branch2_schema

    assert branch2.schema_hash == branch2_schema.get_hash_full()

    # Validate that we can't create a branch with a name that already exist
    result = await graphql(
        schema,
        source=query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )
    assert len(result.errors) == 1
    assert "The branch branch2, already exist" in result.errors[0].message

    # Create another branch with different inputs
    query = """
    mutation {
        BranchCreate(data: { name: "branch3", description: "my description" }) {
            ok
            object {
                id
                name
                description
                is_data_only
            }
        }
    }
    """
    result = await graphql(
        schema,
        source=query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )

    assert result.errors is None
    assert result.data["BranchCreate"]["ok"] is True
    assert len(result.data["BranchCreate"]["object"]["id"]) == 36  # lenght of an UUID
    assert result.data["BranchCreate"]["object"]["name"] == "branch3"
    assert result.data["BranchCreate"]["object"]["description"] == "my description"
    assert result.data["BranchCreate"]["object"]["is_data_only"] is False


async def test_branch_create_registry(
    db, session, default_branch: Branch, car_person_schema, register_core_models_schema
):
    schema = await generate_graphql_schema(branch=default_branch, session=session, include_subscription=False)

    query = """
    mutation {
        BranchCreate(data: { name: "branch2", is_data_only: true }) {
            ok
            object {
                id
                name
                description
                is_data_only
                is_default
                branched_from
            }
        }
    }
    """
    result = await graphql(
        schema,
        source=query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )

    assert result.errors is None
    assert result.data["BranchCreate"]["ok"] is True

    branch2 = await Branch.get_by_name(session=session, name="branch2")
    assert branch2.schema_hash.main == default_branch.schema_hash.main


async def test_branch_query(db, session, default_branch: Branch, car_person_schema, register_core_models_schema):
    schema = await generate_graphql_schema(branch=default_branch, session=session, include_subscription=False)

    create_branch = """
    mutation {
        BranchCreate(data: { name: "branch3", description: "my description" }) {
            ok
            object {
                id
                name
            }
        }
    }
    """
    branch3_result = await graphql(
        schema,
        source=create_branch,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )
    branch3 = branch3_result.data["BranchCreate"]["object"]
    query = """
    query {
        Branch {
            id
            name
        }
    }
    """
    all_branches = await graphql(
        schema,
        source=query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )
    name_query = (
        """
    query {
        Branch(name: "%s" ) {
            id
            name
        }
    }
    """
        % branch3["name"]
    )
    name_response = await graphql(
        schema,
        source=name_query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )
    id_query = """
    query {
        Branch(ids: %s ) {
            id
            name
        }
    }
    """ % [
        branch3["id"]
    ]
    id_query = id_query.replace("'", '"')

    id_response = await graphql(
        schema,
        source=id_query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )

    assert len(all_branches.data["Branch"]) == 2
    assert len(name_response.data["Branch"]) == 1
    assert len(id_response.data["Branch"]) == 1
    assert name_response.data["Branch"][0]["name"] == "branch3"
    assert id_response.data["Branch"][0]["name"] == "branch3"


async def test_branch_create_invalid_names(
    db, session, default_branch: Branch, car_person_schema, register_core_models_schema
):
    schema = await generate_graphql_schema(branch=default_branch, session=session, include_subscription=False)

    query = """
    mutation($branch_name: String!) {
        BranchCreate(data: { name: $branch_name, is_data_only: true }) {
            ok
            object {
                id
                name
            }
        }
    }
    """
    result = await graphql(
        schema,
        source=query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={"branch_name": "not valid"},
    )

    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == "Branch name contains invalid patterns or characters: disallowed ASCII characters/patterns"
    )


async def test_branch_create_with_repositories(
    db, session, default_branch: Branch, rpc_client, repos_and_checks_in_main, register_core_models_schema, data_schema
):
    query = """
    mutation {
        BranchCreate(data: { name: "branch2", is_data_only: false }) {
            ok
            object {
                id
                name
            }
        }
    }
    """
    result = await graphql(
        await generate_graphql_schema(branch=default_branch, session=session, include_subscription=False),
        source=query,
        context_value={"infrahub_session": session, "infrahub_database": db, "infrahub_rpc_client": rpc_client},
        root_value=None,
        variable_values={},
    )

    assert result.errors is None
    assert result.data["BranchCreate"]["ok"] is True
    assert len(result.data["BranchCreate"]["object"]["id"]) == 36  # lenght of an UUID

    assert await Branch.get_by_name(session=session, name="branch2")


async def test_branch_rebase(db, session, default_branch: Branch, group_graphql, car_person_schema):
    branch2 = await create_branch(session=session, branch_name="branch2")

    query = """
    mutation {
        BranchRebase(data: { name: "branch2" }) {
            ok
            object {
                id
            }
        }
    }
    """
    result = await graphql(
        await generate_graphql_schema(branch=default_branch, session=session, include_subscription=False),
        source=query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )

    assert result.errors is None
    assert result.data["BranchRebase"]["ok"] is True
    assert result.data["BranchRebase"]["object"]["id"] == str(branch2.uuid)

    new_branch2 = await Branch.get_by_name(session=session, name="branch2")
    assert new_branch2.branched_from != branch2.branched_from


async def test_branch_rebase_wrong_branch(db, session, default_branch: Branch, group_graphql, car_person_schema):
    query = """
    mutation {
        BranchRebase(data: { name: "branch2" }) {
            ok
            object {
                id
            }
        }
    }
    """
    result = await graphql(
        await generate_graphql_schema(branch=default_branch, session=session, include_subscription=False),
        source=query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )

    assert len(result.errors) == 1
    assert result.errors[0].message == "Branch: branch2 not found."


async def test_branch_validate(db, session, base_dataset_02, register_core_models_schema):
    branch1 = await Branch.get_by_name(session=session, name="branch1")

    query = """
    mutation {
        BranchValidate(data: { name: "branch1" }) {
            ok
            object {
                id
            }
        }
    }
    """
    result = await graphql(
        await generate_graphql_schema(branch=branch1, session=session, include_subscription=False),
        source=query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )

    assert result.errors is None
    assert result.data["BranchValidate"]["ok"] is True
    assert result.data["BranchValidate"]["object"]["id"] == str(branch1.uuid)


async def test_branch_update(db, session, base_dataset_02):
    branch4 = await create_branch("branch4", session)

    query = """
    mutation {
    BranchUpdate(
        data: {
        name: "branch4",
        description: "testing"
        }
    ) {
        ok
    }
    }
    """

    result = await graphql(
        await generate_graphql_schema(branch=branch4, session=session, include_subscription=False),
        source=query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )

    assert result.errors is None
    assert result.data["BranchUpdate"]["ok"] is True

    branch4_updated = await Branch.get_by_name(session=session, name="branch4")

    assert branch4_updated.description == "testing"


async def test_branch_merge(db, session, base_dataset_02, register_core_models_schema):
    branch1 = await Branch.get_by_name(session=session, name="branch1")

    query = """
    mutation {
        BranchMerge(data: { name: "branch1" }) {
            ok
            object {
                id
            }
        }
    }
    """
    result = await graphql(
        await generate_graphql_schema(branch=branch1, session=session, include_subscription=False),
        source=query,
        context_value={"infrahub_session": session, "infrahub_database": db},
        root_value=None,
        variable_values={},
    )

    assert result.errors is None
    assert result.data["BranchMerge"]["ok"] is True
    assert result.data["BranchMerge"]["object"]["id"] == str(branch1.uuid)
