from gevent import monkey

monkey.patch_socket()
monkey.patch_ssl()

from ._connection import Connection

__version__ = '0.0.7'
