from __future__ import annotations

from typing import TYPE_CHECKING, Any

from infrahub_client import Timestamp as BaseTimestamp

if TYPE_CHECKING:
    from pendulum.datetime import DateTime


class Timestamp(BaseTimestamp):
    async def to_graphql(self, *args: Any, **kwargs: Any) -> DateTime:  # pylint: disable=unused-argument
        return self.obj
