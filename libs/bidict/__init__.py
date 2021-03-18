# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#==============================================================================
#                    * Welcome to the bidict source code *
#==============================================================================

# Doing a code review? You'll find a "Code review nav" comment like the one
# below at the top and bottom of the most important source files. This provides
# a suggested initial path through the source when reviewing.
#
# Note: If you aren't reading this on https://github.com/jab/bidict, you may be
# viewing an outdated version of the code. Please head to GitHub to review the
# latest version, which contains important improvements over older versions.
#
# Thank you for reading and for any feedback you provide.

#                             * Code review nav *
#==============================================================================
#                             Current: __init__.py            Next: _abc.py →
#==============================================================================


"""The bidirectional mapping library for Python.

bidict by example:

.. code-block:: python

   >>> from bidict import bidict
   >>> element_by_symbol = bidict({'H': 'hydrogen'})
   >>> element_by_symbol['H']
   'hydrogen'
   >>> element_by_symbol.inverse['hydrogen']
   'H'


Please see https://github.com/jab/bidict for the most up-to-date code and
https://bidict.readthedocs.io for the most up-to-date documentation
if you are reading this elsewhere.


.. :copyright: (c) 2009-2020 Joshua Bronson.
.. :license: MPLv2. See LICENSE for details.
"""

# Use private aliases to not re-export these publicly (for Sphinx automodule with imported-members).
from sys import version_info as _version_info


if _version_info < (3, 6):  # pragma: no cover
    raise ImportError('Python 3.6+ is required.')

# The rest of this file only collects functionality implemented in the rest of the
# source for the purposes of exporting it under the `bidict` module namespace.
# flake8: noqa: F401 (imported but unused)
from ._abc import BidirectionalMapping, MutableBidirectionalMapping
from ._base import BidictBase
from ._mut import MutableBidict
from ._bidict import bidict
from ._frozenbidict import frozenbidict
from ._frozenordered import FrozenOrderedBidict
from ._named import namedbidict
from ._orderedbase import OrderedBidictBase
from ._orderedbidict import OrderedBidict
from ._dup import ON_DUP_DEFAULT, ON_DUP_RAISE, ON_DUP_DROP_OLD, RAISE, DROP_OLD, DROP_NEW, OnDup, OnDupAction
from ._exc import BidictException, DuplicationError, KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError
from ._iter import inverted
from .metadata import (
    __author__, __maintainer__, __copyright__, __email__, __credits__, __url__,
    __license__, __status__, __description__, __keywords__, __version__, __version_info__,
)

# Set __module__ of re-exported classes to the 'bidict' top-level module name
# so that private/internal submodules are not exposed to users e.g. in repr  strings.
_locals = tuple(locals().items())
for _name, _obj in _locals:  # pragma: no cover
    if not getattr(_obj, '__module__', '').startswith('bidict.'):
        continue
    try:
        _obj.__module__ = 'bidict'
    except AttributeError as exc:  # raised when __module__ is read-only (as in OnDup)
        pass


#                             * Code review nav *
#==============================================================================
#                             Current: __init__.py            Next: _abc.py →
#==============================================================================
