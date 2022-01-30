import datetime
import json
import os

from kombu import Connection, Exchange

RABBITMQ_URI = os.getenv("RABBITMQ_URI")


class Command:
    name: str

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class CreateGroup(Command):
    name = "create_group"

    def __call__(self, *args, username, group_name: str, **kwargs):
        message = {
            "type": "create_group",
            "timestamp": datetime.datetime.now().isoformat(),
            "payload": {
                "group_name": group_name,
                "username": username,
            }
        }

        with Connection(RABBITMQ_URI) as conn:
            conn.Producer().publish(
                json.dumps(message),
                exchange=Exchange("commands"),
                content_type="application/json",
                serializer="json"
            )


class JoinGroup(Command):
    name = "append_user_to_group"

    def __call__(self, *args, username: str, group_name: str, **kwargs):
        message = {
            "type": "append_user_to_group",
            "timestamp": datetime.datetime.now().isoformat(),
            "payload": {
                "group_name": group_name,
                "username": username
            }
        }
        with Connection(RABBITMQ_URI) as conn:
            conn.Producer().publish(
                json.dumps(message),
                exchange=Exchange("commands"),
                content_type="application/json",
                serializer="json"
            )


class DeleteGroup(Command):
    name = "delete_group"

    def __call__(self, *args, username: str, group_name: str, **kwargs):
        message = {
            "type": "delete_group",
            "timestamp": datetime.datetime.now().isoformat(),
            "payload": {
                "group_name": group_name,
                "username": username
            }
        }
        with Connection(RABBITMQ_URI) as conn:
            conn.Producer().publish(
                json.dumps(message),
                exchange=Exchange("commands"),
                content_type="application/json",
                serializer="json"
            )
