from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .m001_add_version_to_graph import Migration001

if TYPE_CHECKING:
    from infrahub.core.root import Root

    from .base import InfrahubMigration

MIGRATIONS = [
    Migration001,
]


async def get_migrations(root: Root) -> Sequence[InfrahubMigration]:
    applicable_migrations = []
    for migration_class in MIGRATIONS:
        migration = migration_class()
        if root.graph_version > migration.minimum_version:
            continue
        applicable_migrations.append(migration)

    return applicable_migrations
