import warnings

from watchdog.observers import Observer

try:
    from .observers import GeventEmitter, GeventObserver

    Observer = GeventObserver
except (ImportError, RuntimeError) as e:  # pragma: no cover
    warnings.warn(str(e), ImportWarning, stacklevel=2)


__version__ = "0.1.1"
__all__ = [
    "GeventEmitter",
    "GeventObserver",
    "Observer",
    "__version__"
]
