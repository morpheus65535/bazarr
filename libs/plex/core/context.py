from threading import Lock


class Context(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __getattr__(self, key):
        return self.kwargs.get(key)


class ContextStack(object):
    def __init__(self):
        self._list = []
        self._lock = Lock()

    def pop(self):
        context = self._list.pop()

        self._lock.release()
        return context

    def push(self, **kwargs):
        self._lock.acquire()

        return self._list.append(Context(**kwargs))
