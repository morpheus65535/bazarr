from .backends import register_backend
from .region import CacheRegion
from .region import make_region
from .. import __version__

# backwards compat

__all__ = [
    "CacheRegion",
    "make_region",
    "register_backend",
    "__version__",
]
