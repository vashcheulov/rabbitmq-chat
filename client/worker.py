from logging import getLogger
from typing import Callable, Type

from kombu import Connection, Consumer as KombuConsumer, Queue
from kombu.mixins import ConsumerProducerMixin

logger = getLogger(__name__)


class ClientWorker(ConsumerProducerMixin):

    def __init__(self, connection: Connection, queue: Queue, group: str, callback: Callable):
        self.connection = connection
        self.queue = queue
        self.group = group
        self.callback = callback

    def on_connection_error(self, exc, interval):
        logger.warning(exc)

    def get_consumers(self, Consumer: Type[KombuConsumer], channel):
        return [
            Consumer(
                queues=self.queue,
                accept=['json'],
                callbacks=[self.handle_message],
                prefetch_count=1000
            )
        ]

    def handle_message(self, body, message):
        sender_username = body["sender_username"]
        group_name = body["group_name"]
        msg = body["message"]
        timestamp = body["timestamp"]
        with open('errors.txt', 'a') as errors:
            errors.write(str(body))
        try:
            if self.group == group_name:
                self.callback(f"[{timestamp}] {sender_username}:{msg}")
        except Exception as exc:
            logger.error(exc)
