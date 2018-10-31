import logging

log = logging.getLogger(__name__)

__version__ = '0.7.0'


try:
    from plex.client import Plex
except Exception as ex:
    log.warn('Unable to import submodules - %s', ex, exc_info=True)
