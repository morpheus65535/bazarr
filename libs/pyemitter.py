import logging

# concurrent.futures is optional
try:
    from concurrent.futures import ThreadPoolExecutor
except ImportError:
    ThreadPoolExecutor = None


log = logging.getLogger(__name__)


class Emitter(object):
    threading = False
    threading_workers = 2

    __constructed = False
    __name = None

    __callbacks = None
    __threading_pool = None

    def __ensure_constructed(self):
        if self.__constructed:
            return

        self.__callbacks = {}
        self.__constructed = True

        if self.threading:
            if ThreadPoolExecutor is None:
                raise Exception('concurrent.futures is required for threading')

            self.__threading_pool = ThreadPoolExecutor(max_workers=self.threading_workers)

    def __log(self, message, *args, **kwargs):
        if self.__name is None:
            self.__name = '%s.%s' % (
                self.__module__,
                self.__class__.__name__
            )

        log.debug(
            ('[%s]:' % self.__name.ljust(34)) + str(message),
            *args, **kwargs
        )

    def __wrap(self, callback, *args, **kwargs):
        def wrap(func):
            callback(func=func, *args, **kwargs)
            return func

        return wrap

    def on(self, events, func=None, on_bound=None):
        if not func:
            # assume decorator, wrap
            return self.__wrap(self.on, events, on_bound=on_bound)

        if not isinstance(events, (list, tuple)):
            events = [events]

        self.__log('on(events: %s, func: %s)', repr(events), repr(func))

        self.__ensure_constructed()

        for event in events:
            if event not in self.__callbacks:
                self.__callbacks[event] = []

            # Bind callback to event
            self.__callbacks[event].append(func)

        # Call 'on_bound' callback
        if on_bound:
            self.__call(on_bound, kwargs={
                'func': func
            })

        return self

    def once(self, event, func=None):
        if not func:
            # assume decorator, wrap
            return self.__wrap(self.once, event)

        self.__log('once(event: %s, func: %s)', repr(event), repr(func))

        def once_callback(*args, **kwargs):
            self.off(event, once_callback)
            func(*args, **kwargs)

        self.on(event, once_callback)

        return self

    def off(self, event=None, func=None):
        self.__log('off(event: %s, func: %s)', repr(event), repr(func))

        self.__ensure_constructed()

        if event and event not in self.__callbacks:
            return self

        if func and func not in self.__callbacks[event]:
            return self

        if event and func:
            self.__callbacks[event].remove(func)
        elif event:
            self.__callbacks[event] = []
        elif func:
            raise ValueError('"event" is required if "func" is specified')
        else:
            self.__callbacks = {}

        return self

    def emit(self, event, *args, **kwargs):
        suppress = kwargs.pop('__suppress', False)

        if not suppress:
            self.__log('emit(event: %s, args: %s, kwargs: %s)', repr(event), repr_trim(args), repr_trim(kwargs))

        self.__ensure_constructed()

        if event not in self.__callbacks:
            return

        for callback in list(self.__callbacks[event]):
            self.__call(callback, args, kwargs, event)

        return self

    def emit_on(self, event, *args, **kwargs):
        func = kwargs.pop('func', None)

        if not func:
            # assume decorator, wrap
            return self.__wrap(self.emit_on, event, *args, **kwargs)

        self.__log('emit_on(event: %s, func: %s, args: %s, kwargs: %s)', repr(event), repr(func), repr(args), repr(kwargs))

        # Bind func from wrapper
        self.on(event, func)

        # Emit event (calling 'func')
        self.emit(event, *args, **kwargs)

    def pipe(self, events, other):
        if type(events) is not list:
            events = [events]

        self.__log('pipe(events: %s, other: %s)', repr(events), repr(other))

        self.__ensure_constructed()

        for event in events:
            self.on(event, PipeHandler(event, other.emit))

        return self

    def __call(self, callback, args=None, kwargs=None, event=None):
        args = args or ()
        kwargs = kwargs or {}

        if self.threading:
            return self.__call_async(callback, args, kwargs, event)

        return self.__call_sync(callback, args, kwargs, event)

    @classmethod
    def __call_sync(cls, callback, args=None, kwargs=None, event=None):
        try:
            callback(*args, **kwargs)
            return True
        except Exception as ex:
            log.warn('[%s] Exception raised in: %s - %s' % (event, cls.__function_name(callback), ex), exc_info=True)
            return False

    def __call_async(self, callback, args=None, kwargs=None, event=None):
        self.__threading_pool.submit(self.__call_sync, callback, args, kwargs, event)

    @staticmethod
    def __function_name(func):
        fragments = []

        # Try append class name
        cls = getattr(func, 'im_class', None)

        if cls and hasattr(cls, '__name__'):
            fragments.append(cls.__name__)

        # Append function name
        fragments.append(func.__name__)

        return '.'.join(fragments)


class PipeHandler(object):
    def __init__(self, event, callback):
        self.event = event
        self.callback = callback

    def __call__(self, *args, **kwargs):
        self.callback(self.event, *args, **kwargs)


def on(emitter, event, func=None):
    emitter.on(event, func)

    return {
        'destroy': lambda: emitter.off(event, func)
    }


def once(emitter, event, func=None):
    return emitter.once(event, func)


def off(emitter, event, func=None):
    return emitter.off(event, func)


def emit(emitter, event, *args, **kwargs):
    return emitter.emit(event, *args, **kwargs)


def repr_trim(value, length=1000):
    value = repr(value)

    if len(value) < length:
        return value

    return '<%s - %s characters>' % (type(value).__name__, len(value))
