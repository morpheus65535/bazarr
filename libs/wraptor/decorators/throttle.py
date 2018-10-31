from functools import wraps
from wraptor import context

class throttle(object):
    """ Throttle a function to execute at most 1 time per <seconds> seconds
        The function is executed on the forward edge.
    """
    def __init__(self, seconds=1, instance_method=False):
        self.throttler = context.throttle(seconds=seconds)
        self.seconds = seconds
        self.instance_method = instance_method

    def __call__(self, fn):
        if self.instance_method:
            @wraps(fn)
            def rewrite_instance_method(instance, *args, **kwargs):
                # the first time we are called we overwrite the method
                # on the class instance with a new memoize instance
                if hasattr(instance, fn.__name__):
                    bound_fn = fn.__get__(instance, instance.__class__)
                    new_throttler = throttle(self.seconds)(bound_fn)
                    setattr(instance, fn.__name__, new_throttler)
                    return getattr(instance, fn.__name__)(*args, **kwargs)

            return rewrite_instance_method

        @wraps(fn)
        def wrapped(*args, **kwargs):
            with self.throttler:
                return fn(*args, **kwargs)
        return wrapped
