class BaseReconnection(object):
    def __init__(self):  # pragma: no cover
        self.reconnecting = False

    def next(self):  # pragma: no cover
        raise NotImplementedError()

    def reset(self):  # pragma: no cover
        raise NotImplementedError()
