from importlib import metadata

from .api import TrakItApi as TrakItApi
from .api import trakit as trakit

__title__ = metadata.metadata(__package__)['name']
__version__ = metadata.version(__package__)
__short_version__ = '.'.join(__version__.split('.')[:2])
__author__ = metadata.metadata(__package__)['author']
__license__ = metadata.metadata(__package__)['License-Expression'] or metadata.metadata(__package__)['license']

del metadata
