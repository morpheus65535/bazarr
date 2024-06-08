
# built-in
from typing import Callable, Optional, TypeVar


T = TypeVar('T')
SimFunc = Optional[Callable[[T, T], float]]
TestFunc = Optional[Callable[[T, T], bool]]
