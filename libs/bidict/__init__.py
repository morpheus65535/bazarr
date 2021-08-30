# -*- coding: utf-8 -*-
# Copyright 2009-2019 Joshua Bronson. All Rights Reserved.
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


"""
Efficient, Pythonic bidirectional map implementation and related functionality.

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


.. :copyright: (c) 2019 Joshua Bronson.
.. :license: MPLv2. See LICENSE for details.
"""

# This __init__.py only collects functionality implemented in the rest of the
# source and exports it under the `bidict` module namespace (via `__all__`).

from ._abc import BidirectionalMapping
from ._base import BidictBase
from ._mut import MutableBidict
from ._bidict import bidict
from ._dup import DuplicationPolicy, IGNORE, OVERWRITE, RAISE
from ._exc import (
    BidictException, DuplicationError,
    KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError)
from ._util import inverted
from ._frozenbidict import frozenbidict
from ._frozenordered import FrozenOrderedBidict
from ._named import namedbidict
from ._orderedbase import OrderedBidictBase
from ._orderedbidict import OrderedBidict
from .metadata import (
    __author__, __maintainer__, __copyright__, __email__, __credits__, __url__,
    __license__, __status__, __description__, __keywords__, __version__, __version_info__)


__all__ = (
    '__author__',
    '__maintainer__',
    '__copyright__',
    '__email__',
    '__credits__',
    '__license__',
    '__status__',
    '__description__',
    '__keywords__',
    '__url__',
    '__version__',
    '__version_info__',
    'BidirectionalMapping',
    'BidictException',
    'DuplicationPolicy',
    'IGNORE',
    'OVERWRITE',
    'RAISE',
    'DuplicationError',
    'KeyDuplicationError',
    'ValueDuplicationError',
    'KeyAndValueDuplicationError',
    'BidictBase',
    'MutableBidict',
    'frozenbidict',
    'bidict',
    'namedbidict',
    'FrozenOrderedBidict',
    'OrderedBidictBase',
    'OrderedBidict',
    'inverted',
)


#                             * Code review nav *
#==============================================================================
#                             Current: __init__.py            Next: _abc.py →
#==============================================================================
