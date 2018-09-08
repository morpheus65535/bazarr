# Cork - Authentication module for the Bottle web framework
# Copyright (C) 2013 Federico Ceratto and others, see AUTHORS file.
# Released under LGPLv3+ license, see LICENSE.txt

"""
.. module:: backend.py
   :synopsis: Base Backend.
"""

class BackendIOException(Exception):
    """Generic Backend I/O Exception"""
    pass

def ni(*args, **kwargs):
    raise NotImplementedError

class Backend(object):
    """Base Backend class - to be subclassed by real backends."""
    save_users = ni
    save_roles = ni
    save_pending_registrations = ni

class Table(object):
    """Base Table class - to be subclassed by real backends."""
    __len__ = ni
    __contains__ = ni
    __setitem__ = ni
    __getitem__ = ni
    __iter__ = ni
    iteritems = ni

