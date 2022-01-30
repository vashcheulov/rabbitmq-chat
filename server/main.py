import logging
import os
from logging import getLogger

from kombu import Connection

from storages import InMemoryGroupStorage
from worker import ServerWorker

logger = getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    rabbitmq_uri = os.getenv("RABBITMQ_URI")
    group_storage = InMemoryGroupStorage()

    with Connection(rabbitmq_uri) as conn:
        logger.info("Starting server worker...")
        try:
            ServerWorker(conn, group_storage).run()
        except KeyboardInterrupt:
            logger.info("Stopping server worker...")
