from storages import GroupsStorage


class Command:

    @property
    def label(self) -> str:
        raise NotImplementedError

    def __call__(self, *args, **kwargs) -> None:
        raise NotImplementedError


class CreateGroup(Command):
    label = "create_group"

    def __init__(self, group_storage: GroupsStorage) -> None:
        self.group_storage = group_storage

    def __call__(self, *args, group_name: str, **kwargs) -> None:
        self.group_storage.register_group(group_name)


class AppendUserToGroup(Command):
    label = "append_user_to_group"

    def __init__(self, group_storage: GroupsStorage) -> None:
        self.group_storage = group_storage

    def __call__(self, *args, group_name: str, username: str, **kwargs) -> None:
        self.group_storage.append_user(group_name, username)


class DeleteGroup(Command):
    label = "delete_group"

    def __init__(self, group_storage: GroupsStorage) -> None:
        self.group_storage = group_storage

    def __call__(self, *args, group_name: str, username: str, **kwargs) -> None:
        self.group_storage.delete_group(group_name, username)
