import logging
from collections.abc import Callable, Mapping, Sequence
from typing import ParamSpec, TypeVar

_P = ParamSpec("_P")
_R = TypeVar("_R")
_Exceptions = type[Exception] | tuple[type[Exception], ...]
_Jitter = float | tuple[float, float]


def retry(
    exceptions: _Exceptions = ...,
    tries: int = ...,
    delay: float = ...,
    max_delay: float | None = ...,
    backoff: float = ...,
    jitter: _Jitter = ...,
    logger: logging.Logger | None = ...,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...


def retry_call(
    f: Callable[..., _R],
    fargs: Sequence[object] | None = ...,
    fkwargs: Mapping[str, object] | None = ...,
    exceptions: _Exceptions = ...,
    tries: int = ...,
    delay: float = ...,
    max_delay: float | None = ...,
    backoff: float = ...,
    jitter: _Jitter = ...,
    logger: logging.Logger | None = ...,
) -> _R | None: ...
