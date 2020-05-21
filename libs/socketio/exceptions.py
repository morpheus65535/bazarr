class SocketIOError(Exception):
    pass


class ConnectionError(SocketIOError):
    pass


class ConnectionRefusedError(ConnectionError):
    """Connection refused exception.

    This exception can be raised from a connect handler when the connection
    is not accepted. The positional arguments provided with the exception are
    returned with the error packet to the client.
    """
    def __init__(self, *args):
        if len(args) == 0:
            self.error_args = None
        elif len(args) == 1 and not isinstance(args[0], list):
            self.error_args = args[0]
        else:
            self.error_args = args


class TimeoutError(SocketIOError):
    pass


class BadNamespaceError(SocketIOError):
    pass
