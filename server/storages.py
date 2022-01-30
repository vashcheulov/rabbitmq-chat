from dataclasses import dataclass
from typing import List

from errors import GroupNotFound


@dataclass
class User:
    username: str


@dataclass
class Group:
    name: str
    users: List[User]


class GroupsStorage:

    def fetch_groups(self) -> List[Group]:
        raise NotImplementedError

    def find_group(self, group_name: str) -> Group:
        raise NotImplementedError

    def register_group(self, group_name: str) -> None:
        raise NotImplementedError

    def append_user(self, group_name: str, username: str) -> None:
        raise NotImplementedError

    def delete_group(self, group_name: str, username: str) -> None:
        raise NotImplementedError


class InMemoryGroupStorage(GroupsStorage):

    def __init__(self):
        self._groups = []

    def fetch_groups(self) -> List[Group]:
        return self._groups

    def find_group(self, group_name: str) -> Group:
        for group in self._groups:
            if group.name == group_name:
                return group
        raise GroupNotFound

    def register_group(self, group_name: str) -> None:
        self._groups.append(
            Group(name=group_name, users=[])
        )

    def append_user(self, group_name: str, username: str) -> None:
        group = self.find_group(group_name)
        group.users.append(User(username=username))

    def delete_group(self, group_name: str, username: str) -> None:
        for index, group in enumerate(self._groups):
            if group.name == group_name:
                self._groups.pop(index)
                break


