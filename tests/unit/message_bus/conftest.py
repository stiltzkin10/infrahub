import pytest

import time
import json
from copy import copy
from datetime import datetime

import uuid

import pickle

from infrahub.message_bus.events import InfrahubMessage
from infrahub.message_bus.events import (
    get_event_exchange,
    MessageType,
    InfrahubMessage,
    InfrahubDataMessage,
    InfrahubGitRPC,
    DataMessageAction,
)


from aio_pika import DeliveryMode, Message


@pytest.fixture
def incoming_data_message_01():

    body = {
        "action": DataMessageAction.CREATE.value,
        "branch": "main",
        "node_id": str(uuid.uuid4()),
        "node_kind": "device",
    }

    return Message(
        body=pickle.dumps(body),
        content_type="application/python-pickle",
        # content_encoding="text",
        delivery_mode=DeliveryMode.PERSISTENT,
        message_id=str(uuid.uuid4()),
        timestamp=datetime.utcfromtimestamp(int(time.time())),
        type=MessageType.DATA.value,
    )
