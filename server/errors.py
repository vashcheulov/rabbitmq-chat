class ServerWorkerError(Exception):
    pass


class GroupNotFound(ServerWorkerError):
    pass


class UnknownAction(ServerWorkerError):
    pass
