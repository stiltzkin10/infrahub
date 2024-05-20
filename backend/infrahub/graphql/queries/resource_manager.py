from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from graphene import Field, Float, Int, List, ObjectType, String
from infrahub_sdk.utils import extract_fields_first_node

from infrahub.core import registry
from infrahub.core.constants import InfrahubKind
from infrahub.core.ipam.utilization import PrefixUtilizationGetter
from infrahub.core.manager import NodeManager
from infrahub.exceptions import NodeNotFoundError

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

    from infrahub.core.node import Node
    from infrahub.database import InfrahubDatabase
    from infrahub.graphql import GraphqlContext


class IPPoolUtilizationResource(ObjectType):
    id = Field(String, required=True, description="The ID of the current resource")
    display_label = Field(String, required=True, description="The common name of the resource")
    kind = Field(String, required=True, description="The resource kind")
    weight = Field(Int, required=True, description="The relative weight of this resource.")
    utilization = Field(Float, required=True, description="The overall utilization of the resource.")
    utilization_branches = Field(
        Float, required=True, description="The utilization of the resource on all non default branches."
    )
    utilization_default_branch = Field(
        Float, required=True, description="The overall utilization of the resource isolated to the default branch."
    )


class IPPrefixUtilizationEdge(ObjectType):
    node = Field(IPPoolUtilizationResource, required=True)


class PoolAllocatedNode(ObjectType):
    id = Field(String, required=True, description="The ID of the allocated node")
    display_label = Field(String, required=True, description="The common name of the resource")
    kind = Field(String, required=True, description="The node kind")
    branch = Field(String, required=True, description="The branch where the node is allocated")
    identifier = Field(String, required=False, description="Identifier used for the allocation")


class PoolAllocatedEdge(ObjectType):
    node = Field(PoolAllocatedNode, required=True)


def _validate_pool_type(pool_id: str, pool: Optional[Node] = None) -> None:
    if not pool or pool._schema.kind not in [InfrahubKind.IPADDRESSPOOL, InfrahubKind.PREFIXPOOL]:
        raise NodeNotFoundError(node_type="ResourcePool", identifier=pool_id)


class PoolAllocated(ObjectType):
    count = Field(Int, required=True, description="The number of allocations within the selected pool.")
    edges = Field(List(of_type=PoolAllocatedEdge, required=True), required=True)

    @staticmethod
    async def resolve(  # pylint: disable=unused-argument
        root: dict,
        info: GraphQLResolveInfo,
        pool_id: str,
        resource_id: str,
        offset: int = 0,
        limit: int = 10,
    ) -> dict:
        context: GraphqlContext = info.context
        pool = await NodeManager.get_one(id=pool_id, db=context.db, branch=context.branch)

        _validate_pool_type(pool_id=pool_id, pool=pool)

        return {
            "count": 2,
            "edges": [
                {
                    "node": {
                        "id": "imaginary-id-1",
                        "kind": "IpamIPPrefix",
                        "display_label": "10.24.16.0/18",
                        "branch": "main",
                        "identifier": "device1__dhcpA",
                    }
                },
                {
                    "node": {
                        "id": "imaginary-id-2",
                        "kind": "IpamIPPrefix",
                        "display_label": "10.28.0.0/16",
                        "branch": "branch1",
                        "identifier": None,
                    }
                },
            ],
        }


class PoolUtilization(ObjectType):
    count = Field(Int, required=True, description="The number of resources within the selected pool.")
    utilization = Field(Float, required=True, description="The overall utilization of the pool.")
    utilization_branches = Field(Float, required=True, description="The utilization in all non default branches.")
    utilization_default_branch = Field(
        Float, required=True, description="The overall utilization of the pool isolated to the default branch."
    )
    edges = Field(List(of_type=IPPrefixUtilizationEdge, required=True), required=True)

    @staticmethod
    async def resolve(  # pylint: disable=unused-argument,too-many-branches
        root: dict,
        info: GraphQLResolveInfo,
        pool_id: str,
    ) -> dict:
        context: GraphqlContext = info.context
        db: InfrahubDatabase = context.db
        pool = await NodeManager.get_one(id=pool_id, db=db, branch=context.branch)
        _validate_pool_type(pool_id=pool_id, pool=pool)
        resources_map: dict[str, Node] = await pool.resources.get_peers(db=db, branch_agnostic=True)  # type: ignore[attr-defined,union-attr]
        utilization_getter = PrefixUtilizationGetter(db=db, ip_prefixes=list(resources_map.values()), at=context.at)
        fields = await extract_fields_first_node(info=info)
        response: dict[str, Any] = {}
        total_utilization = None
        default_branch_utilization = None
        if "count" in fields:
            response["count"] = len(resources_map)
        if "utilization" in fields:
            response["utilization"] = total_utilization = await utilization_getter.get_use_percentage()
        if "utilization_default_branch" in fields:
            response["utilization_default_branch"] = (
                default_branch_utilization
            ) = await utilization_getter.get_use_percentage(branch_names=[registry.default_branch])
        if "utilization_branches" in fields:
            total_utilization = (
                total_utilization if total_utilization is not None else await utilization_getter.get_use_percentage()
            )
            default_branch_utilization = (
                default_branch_utilization
                if default_branch_utilization is not None
                else await utilization_getter.get_use_percentage(branch_names=[registry.default_branch])
            )
            response["utilization_branches"] = total_utilization - default_branch_utilization
        if "edges" in fields:
            response["edges"] = []
            if "node" in fields["edges"]:
                node_fields = fields["edges"]["node"]
                for resource_id, resource_node in resources_map.items():
                    resource_total = None
                    default_branch_total = None
                    node_response: dict[str, Union[str, float, int]] = {}
                    if "id" in node_fields:
                        node_response["id"] = resource_id
                    if "kind" in node_fields:
                        node_response["kind"] = resource_node.get_kind()
                    if "display_label" in node_fields:
                        node_response["display_label"] = await resource_node.render_display_label(db=db)
                    if "weight" in node_fields:
                        node_response["weight"] = await resource_node.get_resource_weight(db=db)  # type: ignore[attr-defined]
                    if "utilization" in node_fields:
                        node_response["utilization"] = resource_total = await utilization_getter.get_use_percentage(
                            ip_prefixes=[resource_node]
                        )
                    if "utilization_default_branch" in node_fields:
                        node_response["utilization_default_branch"] = (
                            default_branch_total
                        ) = await utilization_getter.get_use_percentage(
                            ip_prefixes=[resource_node], branch_names=[registry.default_branch]
                        )
                    if "utilization_branches" in node_fields:
                        resource_total = (
                            resource_total
                            if resource_total is not None
                            else await utilization_getter.get_use_percentage(ip_prefixes=[resource_node])
                        )
                        default_branch_total = (
                            default_branch_total
                            if default_branch_total is not None
                            else await utilization_getter.get_use_percentage(
                                ip_prefixes=[resource_node], branch_names=[registry.default_branch]
                            )
                        )
                        node_response["utilization_branches"] = resource_total - default_branch_total
                    response["edges"].append({"node": node_response})

        return response


InfrahubResourcePoolAllocated = Field(
    PoolAllocated,
    pool_id=String(required=True),
    resource_id=String(required=True),
    limit=Int(required=False),
    offset=Int(required=False),
    resolver=PoolAllocated.resolve,
)


InfrahubResourcePoolUtilization = Field(
    PoolUtilization,
    pool_id=String(required=True),
    resolver=PoolUtilization.resolve,
)
