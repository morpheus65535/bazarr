# -*- coding: utf-8 -*-
# Copyright 2009-2019 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Compatibility helpers."""

from operator import methodcaller
from platform import python_implementation
from sys import version_info
from warnings import warn


# Use #: (before or) at the end of each line with a member we want to show up in the docs,
# otherwise Sphinx won't include (even though we configure automodule with undoc-members).

PYMAJOR, PYMINOR = version_info[:2]  #:
PY2 = PYMAJOR == 2  #:
PYIMPL = python_implementation()  #:
CPY = PYIMPL == 'CPython'  #:
PYPY = PYIMPL == 'PyPy'  #:
DICTS_ORDERED = PYPY or (CPY and (PYMAJOR, PYMINOR) >= (3, 6))  #:

# Without the following, pylint gives lots of false positives.
# pylint: disable=invalid-name,unused-import,ungrouped-imports,no-name-in-module

if PY2:
    if PYMINOR < 7:  # pragma: no cover
        raise ImportError('Python 2.7 or 3.5+ is required.')
    warn('Python 2 support will be dropped in a future release.')

    # abstractproperty deprecated in Python 3.3 in favor of using @property with @abstractmethod.
    # Before 3.3, this silently fails to detect when an abstract property has not been overridden.
    from abc import abstractproperty  #:

    from itertools import izip  #:

    # In Python 3, the collections ABCs were moved into collections.abc, which does not exist in
    # Python 2. Support for importing them directly from collections is dropped in Python 3.8.
    import collections as collections_abc  # noqa: F401 (imported but unused)
    from collections import (  # noqa: F401 (imported but unused)
        Mapping, MutableMapping, KeysView, ValuesView, ItemsView)

    viewkeys = lambda m: m.viewkeys() if hasattr(m, 'viewkeys') else KeysView(m)  #:
    viewvalues = lambda m: m.viewvalues() if hasattr(m, 'viewvalues') else ValuesView(m)  #:
    viewitems = lambda m: m.viewitems() if hasattr(m, 'viewitems') else ItemsView(m)  #:

    iterkeys = lambda m: m.iterkeys() if hasattr(m, 'iterkeys') else iter(m.keys())  #:
    itervalues = lambda m: m.itervalues() if hasattr(m, 'itervalues') else iter(m.values())  #:
    iteritems = lambda m: m.iteritems() if hasattr(m, 'iteritems') else iter(m.items())  #:

else:
    # Assume Python 3 when not PY2, but explicitly check before showing this warning.
    if PYMAJOR == 3 and PYMINOR < 5:  # pragma: no cover
        warn('Python 3.4 and below are not supported.')

    import collections.abc as collections_abc  # noqa: F401 (imported but unused)
    from collections.abc import (  # noqa: F401 (imported but unused)
        Mapping, MutableMapping, KeysView, ValuesView, ItemsView)

    viewkeys = methodcaller('keys')  #:
    viewvalues = methodcaller('values')  #:
    viewitems = methodcaller('items')  #:

    def _compose(f, g):
        return lambda x: f(g(x))

    iterkeys = _compose(iter, viewkeys)  #:
    itervalues = _compose(iter, viewvalues)  #:
    iteritems = _compose(iter, viewitems)  #:

    from abc import abstractmethod
    abstractproperty = _compose(property, abstractmethod)  #:

    izip = zip  #:
