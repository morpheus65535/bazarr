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
# ← Prev: _base.py    Current: _delegating_mixins.py   Next: _frozenbidict.py →
#==============================================================================


r"""Provides mixin classes that delegate to ``self._fwdm`` for various operations.

This allows methods such as :meth:`bidict.bidict.items`
to be implemented in terms of a ``self._fwdm.items()`` call,
which is potentially much more efficient (e.g. in CPython 2)
compared to the implementation inherited from :class:`~collections.abc.Mapping`
(which returns ``[(key, self[key]) for key in self]`` in Python 2).

Because this depends on implementation details that aren't necessarily true
(such as the bidict's values being the same as its ``self._fwdm.values()``,
which is not true for e.g. ordered bidicts where ``_fwdm``\'s values are nodes),
these should always be mixed in at a layer below a more general layer,
as they are in e.g. :class:`~bidict.frozenbidict`
which extends :class:`~bidict.BidictBase`.

See the :ref:`extending:Sorted Bidict Recipes`
for another example of where this comes into play.
``SortedBidict`` extends :class:`bidict.MutableBidict`
rather than :class:`bidict.bidict`
to avoid inheriting these mixins,
which are incompatible with the backing
:class:`sortedcontainers.SortedDict`s.
"""

from .compat import PY2


_KEYS_METHODS = ('keys',) + (('viewkeys', 'iterkeys') if PY2 else ())
_ITEMS_METHODS = ('items',) + (('viewitems', 'iteritems') if PY2 else ())
_DOCSTRING_BY_METHOD = {
    'keys': 'A set-like object providing a view on the contained keys.',
    'items': 'A set-like object providing a view on the contained items.',
}
if PY2:
    _DOCSTRING_BY_METHOD['viewkeys'] = _DOCSTRING_BY_METHOD['keys']
    _DOCSTRING_BY_METHOD['viewitems'] = _DOCSTRING_BY_METHOD['items']
    _DOCSTRING_BY_METHOD['keys'] = 'A list of the contained keys.'
    _DOCSTRING_BY_METHOD['items'] = 'A list of the contained items.'


def _make_method(methodname):
    def method(self):
        return getattr(self._fwdm, methodname)()  # pylint: disable=protected-access
    method.__name__ = methodname
    method.__doc__ = _DOCSTRING_BY_METHOD.get(methodname, '')
    return method


def _make_fwdm_delegating_mixin(clsname, methodnames):
    clsdict = dict({name: _make_method(name) for name in methodnames}, __slots__=())
    return type(clsname, (object,), clsdict)


_DelegateKeysToFwdm = _make_fwdm_delegating_mixin('_DelegateKeysToFwdm', _KEYS_METHODS)
_DelegateItemsToFwdm = _make_fwdm_delegating_mixin('_DelegateItemsToFwdm', _ITEMS_METHODS)
_DelegateKeysAndItemsToFwdm = type(
    '_DelegateKeysAndItemsToFwdm',
    (_DelegateKeysToFwdm, _DelegateItemsToFwdm),
    {'__slots__': ()})

#                             * Code review nav *
#==============================================================================
# ← Prev: _base.py    Current: _delegating_mixins.py   Next: _frozenbidict.py →
#==============================================================================
