from importlib import metadata

__title__ = metadata.metadata(__package__)['name']
__version__ = metadata.version(__package__)
__short_version__ = '.'.join(__version__.split('.')[:2])
__author__ = metadata.metadata(__package__)['author']
__license__ = metadata.metadata(__package__)['license']
__url__ = metadata.metadata(__package__)['home_page']

del metadata

from .api import TrakItApi, trakit
