"""Compatibility namespace for those using dogpile.core.

As of dogpile.cache 0.6.0, dogpile.core as a separate package
is no longer used by dogpile.cache.

Note that this namespace will not take effect if an actual
dogpile.core installation is present.

"""

from .util import nameregistry  # noqa
from .util import readwrite_lock  # noqa
from .util.readwrite_lock import ReadWriteMutex  # noqa
from .util.nameregistry import NameRegistry  # noqa
from .lock import Lock  # noqa
from .lock import NeedRegenerationException  # noqa
from . import __version__ # noqa
