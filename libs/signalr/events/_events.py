class EventHook(object):
    def __init__(self):
        self._handlers = []

    def __iadd__(self, handler):
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        self._handlers.remove(handler)
        return self

    def fire(self, *args, **kwargs):
        for handler in self._handlers:
            handler(*args, **kwargs)
