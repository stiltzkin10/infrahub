import typer
import uvicorn

import json

import asyncio
from asyncio import run as aiorun

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message, connect, IncomingMessage

import infrahub.config as config
from infrahub.core.initialization import initialization
from infrahub.core.manager import NodeManager
from infrahub.message_bus import get_broker
from infrahub.message_bus.events import get_event_exchange, EventType, Event, DataEvent

app = typer.Typer()

from rich import print as rprint


async def print_event(event: IncomingMessage) -> None:

    event = Event.init(event)
    rprint(event)


async def _listen(topic: str, config_file: str):

    config.load_and_exit(config_file)

    connection = await get_broker()

    async with connection:

        # Creating a channel
        channel = await connection.channel()

        exchange = await get_event_exchange(channel)

        # Declaring & Binding queue
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(exchange, routing_key=topic)

        await queue.consume(print_event, no_ack=True)

        print(f" Waiting for events matching the topic `{topic}`. To exit press CTRL+C")
        await asyncio.Future()


async def _generate(type: EventType, config_file: str):

    config.load_and_exit(config_file)
    initialization()
    nodes = NodeManager.query("Criticality")

    event = DataEvent(action="create", node=nodes[0])
    await event.send()


@app.command()
def listen(topic: str = "#", config_file: str = typer.Argument("infrahub.toml", envvar="INFRAHUB_CONFIG")):
    """Listen to event in the Events bus and print them."""
    aiorun(_listen(topic=topic, config_file=config_file))


@app.command()
def generate(type: EventType, config_file: str = typer.Argument("infrahub.toml", envvar="INFRAHUB_CONFIG")):
    aiorun(_generate(type, config_file=config_file))
