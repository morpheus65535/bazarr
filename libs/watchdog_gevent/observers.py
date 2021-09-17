import os

from watchdog.events import (
    DirDeletedEvent,
    DirCreatedEvent,
    DirModifiedEvent,
    FileDeletedEvent,
    FileCreatedEvent,
    FileModifiedEvent
)
from watchdog.observers.api import (
    EventEmitter,
    BaseObserver,
    DEFAULT_EMITTER_TIMEOUT,
    DEFAULT_OBSERVER_TIMEOUT
)


try:
    import gevent
    import gevent.monkey
    import gevent.pool
    import gevent.queue
    import gevent.threading
except ImportError:  # pragma: no cover
    raise ImportError(
        "gevent observers require the gevent package. Run "
        "'pip install gevent' and try again."
    )


if not gevent.monkey.is_module_patched("threading"):  # pragma: no cover
    raise RuntimeError(
        "gevent observers require the 'threading' module to be "
        "monkeypatched by gevent."
    )


def _get_contents(path):
    try:
        if os.path.isdir(path):
            return set(os.listdir(path))

        return None
    except Exception:  # pragma: no cover
        return None


class GeventEmitter(EventEmitter):
    """gevent-based emitter.
    """

    def __init__(self, event_queue, watch, timeout=DEFAULT_EMITTER_TIMEOUT):
        EventEmitter.__init__(self, event_queue, watch, timeout)

        self._hub = gevent.get_hub()
        self._watchlist = set()
        self._workers = gevent.pool.Group()
        self._add(watch.path, watch.is_recursive)

    def queue_events(self, timeout):
        gevent.sleep(timeout)

    def _add(self, path, recursive=True):
        if not os.path.isabs(path):
            path = os.path.abspath(path)

        if os.path.isdir(path):
            if recursive:
                for filename in os.listdir(path):
                    self._add(os.path.join(path, filename))

            self._workers.spawn(self._watch_dir, path)
        else:
            self._workers.spawn(self._watch_file, path)

    def _loop(self, path):
        watcher = self._hub.loop.stat(path, self.timeout / 2)

        while path in self._watchlist:
            try:
                with gevent.Timeout(self.timeout):
                    self._hub.wait(watcher)

            except gevent.Timeout:
                continue

            except gevent.hub.LoopExit:
                break

            yield os.path.exists(path)

    def _watch_dir(self, path):
        contents = _get_contents(path)
        if contents is None:
            return

        self._watchlist.add(path)
        for exists in self._loop(path):
            current_contents = _get_contents(path)
            if current_contents is None:
                break

            added_contents = current_contents - contents
            for filename in added_contents:
                filepath = os.path.join(path, filename)
                self._add(filepath)

                if os.path.isdir(filepath):
                    self.queue_event(DirCreatedEvent(filepath))
                else:
                    self.queue_event(FileCreatedEvent(filepath))

            contents = current_contents
            if os.path.exists(path):
                self.queue_event(DirModifiedEvent(path))

        for filename in contents:
            filepath = os.path.join(path, filename)
            self._watchlist.discard(filepath)
        self._watchlist.discard(path)
        self.queue_event(DirDeletedEvent(path))

    def _watch_file(self, path):
        self._watchlist.add(path)
        for exists in self._loop(path):
            if not exists:
                break

            self.queue_event(FileModifiedEvent(path))

        self._watchlist.discard(path)
        self.queue_event(FileDeletedEvent(path))


class GeventObserver(BaseObserver):
    """Observer thread that watches directories using gevent.
    Requires gevent monkeypatching to be turned on before import.
    """

    def __init__(self, timeout=DEFAULT_OBSERVER_TIMEOUT):
        BaseObserver.__init__(
            self,
            timeout=timeout,
            emitter_class=GeventEmitter,
        )
