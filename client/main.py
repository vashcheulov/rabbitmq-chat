import logging
from logging import getLogger

from cli import start

logger = getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start()
