import json
from logging import getLogger
from typing import Type

from kombu import Connection, Consumer as KombuConsumer, Exchange, Queue
from kombu.mixins import ConsumerProducerMixin

from commands import AppendUserToGroup, CreateGroup, DeleteGroup
from storages import GroupsStorage

logger = getLogger(__name__)


class ServerWorker(ConsumerProducerMixin):

    def __init__(self, connection: Connection, group_storage: GroupsStorage):
        self.connection = connection
        self.hub_queue = Queue("hub", exchange=Exchange("hub"))
        self.commands_queue = Queue("commands", exchange=Exchange("commands"))

        self.group_storage = group_storage
        self.commands = [
            CreateGroup(group_storage),
            AppendUserToGroup(group_storage),
            DeleteGroup(group_storage)
        ]

    def on_connection_error(self, exc, interval):
        logger.warning(exc)

    def get_consumers(self, Consumer: Type[KombuConsumer], channel):
        return [
            Consumer(
                queues=self.hub_queue,
                accept=['json'],
                callbacks=[self.handle_message],
                auto_declare=True
            ),
            Consumer(
                queues=self.commands_queue,
                accept=['json'],
                callbacks=[self.handle_command],
                auto_declare=True
            )
        ]

    def handle_message(self, body, message):
        try:
            group_name = body["group_name"]

            self.producer.publish(
                json.dumps(body),
                routing_key=f"group.{group_name}",
                exchange=Exchange(f"group.{group_name}"),
                content_type="application/json",
                serializer="json",
                retry=True
            )
        except Exception as exc:
            logger.error(exc)
        message.ack()

    def handle_command(self, body, message):
        try:
            command_type = body["type"]
            payload = body["payload"]
            for command in self.commands:
                if command_type == command.label:
                    command(**payload)
                    if command_type in [AppendUserToGroup.label, CreateGroup.label]:
                        queue = Queue(
                            name=f"username.{payload['username']}",
                            routing_key=f"group.{payload['group_name']}",
                            exchange=f"group.{payload['group_name']}"
                        )
                        queue.declare(channel=self.connection.channel())
                    logger.info(f"Command '{command_type}' successfully completed")
                    break
            else:
                logger.warning(f"Unknown command: {command_type}")
        except Exception as exc:
            logger.error(exc)

        message.ack()
