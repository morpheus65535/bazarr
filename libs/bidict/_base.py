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
# ← Prev: _abc.py             Current: _base.py   Next: _delegating_mixins.py →
#==============================================================================


"""Provides :class:`BidictBase`."""

from collections import namedtuple
from weakref import ref

from ._abc import BidirectionalMapping
from ._dup import RAISE, OVERWRITE, IGNORE, _OnDup
from ._exc import (
    DuplicationError, KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError)
from ._miss import _MISS
from ._noop import _NOOP
from ._util import _iteritems_args_kw
from .compat import PY2, KeysView, ItemsView, Mapping, iteritems


_DedupResult = namedtuple('_DedupResult', 'isdupkey isdupval invbyval fwdbykey')
_WriteResult = namedtuple('_WriteResult', 'key val oldkey oldval')
_NODUP = _DedupResult(False, False, _MISS, _MISS)


class BidictBase(BidirectionalMapping):
    """Base class implementing :class:`BidirectionalMapping`."""

    __slots__ = ('_fwdm', '_invm', '_inv', '_invweak', '_hash') + (() if PY2 else ('__weakref__',))

    #: The default :class:`DuplicationPolicy`
    #: (in effect during e.g. :meth:`~bidict.bidict.__init__` calls)
    #: that governs behavior when a provided item
    #: duplicates only the key of another item.
    #:
    #: Defaults to :attr:`~bidict.OVERWRITE`
    #: to match :class:`dict`'s behavior.
    #:
    #: *See also* :ref:`basic-usage:Values Must Be Unique`, :doc:`extending`
    on_dup_key = OVERWRITE

    #: The default :class:`DuplicationPolicy`
    #: (in effect during e.g. :meth:`~bidict.bidict.__init__` calls)
    #: that governs behavior when a provided item
    #: duplicates only the value of another item.
    #:
    #: Defaults to :attr:`~bidict.RAISE`
    #: to prevent unintended overwrite of another item.
    #:
    #: *See also* :ref:`basic-usage:Values Must Be Unique`, :doc:`extending`
    on_dup_val = RAISE

    #: The default :class:`DuplicationPolicy`
    #: (in effect during e.g. :meth:`~bidict.bidict.__init__` calls)
    #: that governs behavior when a provided item
    #: duplicates the key of another item and the value of a third item.
    #:
    #: Defaults to ``None``, which causes the *on_dup_kv* policy to match
    #: whatever *on_dup_val* policy is in effect.
    #:
    #: *See also* :ref:`basic-usage:Values Must Be Unique`, :doc:`extending`
    on_dup_kv = None

    _fwdm_cls = dict
    _invm_cls = dict

    #: The object used by :meth:`__repr__` for printing the contained items.
    _repr_delegate = dict

    def __init__(self, *args, **kw):  # pylint: disable=super-init-not-called
        """Make a new bidirectional dictionary.
        The signature is the same as that of regular dictionaries.
        Items passed in are added in the order they are passed,
        respecting the current duplication policies in the process.

        *See also* :attr:`on_dup_key`, :attr:`on_dup_val`, :attr:`on_dup_kv`
        """
        #: The backing :class:`~collections.abc.Mapping`
        #: storing the forward mapping data (*key* → *value*).
        self._fwdm = self._fwdm_cls()
        #: The backing :class:`~collections.abc.Mapping`
        #: storing the inverse mapping data (*value* → *key*).
        self._invm = self._invm_cls()
        self._init_inv()  # lgtm [py/init-calls-subclass]
        if args or kw:
            self._update(True, None, *args, **kw)

    def _init_inv(self):
        # Compute the type for this bidict's inverse bidict (will be different from this
        # bidict's type if _fwdm_cls and _invm_cls are different).
        inv_cls = self._inv_cls()
        # Create the inverse bidict instance via __new__, bypassing its __init__ so that its
        # _fwdm and _invm can be assigned to this bidict's _invm and _fwdm. Store it in self._inv,
        # which holds a strong reference to a bidict's inverse, if one is available.
        self._inv = inv = inv_cls.__new__(inv_cls)
        inv._fwdm = self._invm  # pylint: disable=protected-access
        inv._invm = self._fwdm  # pylint: disable=protected-access
        # Only give the inverse a weak reference to this bidict to avoid creating a reference cycle,
        # stored in the _invweak attribute. See also the docs in
        # :ref:`addendum:Bidict Avoids Reference Cycles`
        inv._inv = None  # pylint: disable=protected-access
        inv._invweak = ref(self)  # pylint: disable=protected-access
        # Since this bidict has a strong reference to its inverse already, set its _invweak to None.
        self._invweak = None

    @classmethod
    def _inv_cls(cls):
        """The inverse of this bidict type, i.e. one with *_fwdm_cls* and *_invm_cls* swapped."""
        if cls._fwdm_cls is cls._invm_cls:
            return cls
        if not getattr(cls, '_inv_cls_', None):
            class _Inv(cls):
                _fwdm_cls = cls._invm_cls
                _invm_cls = cls._fwdm_cls
                _inv_cls_ = cls
            _Inv.__name__ = cls.__name__ + 'Inv'
            cls._inv_cls_ = _Inv
        return cls._inv_cls_

    @property
    def _isinv(self):
        return self._inv is None

    @property
    def inverse(self):
        """The inverse of this bidict.

        *See also* :attr:`inv`
        """
        # Resolve and return a strong reference to the inverse bidict.
        # One may be stored in self._inv already.
        if self._inv is not None:
            return self._inv
        # Otherwise a weakref is stored in self._invweak. Try to get a strong ref from it.
        inv = self._invweak()
        if inv is not None:
            return inv
        # Refcount of referent must have dropped to zero, as in `bidict().inv.inv`. Init a new one.
        self._init_inv()  # Now this bidict will retain a strong ref to its inverse.
        return self._inv

    @property
    def inv(self):
        """Alias for :attr:`inverse`."""
        return self.inverse

    def __getstate__(self):
        """Needed to enable pickling due to use of :attr:`__slots__` and weakrefs.

        *See also* :meth:`object.__getstate__`
        """
        state = {}
        for cls in self.__class__.__mro__:
            slots = getattr(cls, '__slots__', ())
            for slot in slots:
                if hasattr(self, slot):
                    state[slot] = getattr(self, slot)
        # weakrefs can't be pickled.
        state.pop('_invweak', None)  # Added back in __setstate__ via _init_inv call.
        state.pop('__weakref__', None)  # Not added back in __setstate__. Python manages this one.
        return state

    def __setstate__(self, state):
        """Implemented because use of :attr:`__slots__` would prevent unpickling otherwise.

        *See also* :meth:`object.__setstate__`
        """
        for slot, value in iteritems(state):
            setattr(self, slot, value)
        self._init_inv()

    def __repr__(self):
        """See :func:`repr`."""
        clsname = self.__class__.__name__
        if not self:
            return '%s()' % clsname
        return '%s(%r)' % (clsname, self._repr_delegate(iteritems(self)))

    # The inherited Mapping.__eq__ implementation would work, but it's implemented in terms of an
    # inefficient ``dict(self.items()) == dict(other.items())`` comparison, so override it with a
    # more efficient implementation.
    def __eq__(self, other):
        u"""*x.__eq__(other)　⟺　x == other*

        Equivalent to *dict(x.items()) == dict(other.items())*
        but more efficient.

        Note that :meth:`bidict's __eq__() <bidict.bidict.__eq__>` implementation
        is inherited by subclasses,
        in particular by the ordered bidict subclasses,
        so even with ordered bidicts,
        :ref:`== comparison is order-insensitive <eq-order-insensitive>`.

        *See also* :meth:`bidict.FrozenOrderedBidict.equals_order_sensitive`
        """
        if not isinstance(other, Mapping) or len(self) != len(other):
            return False
        selfget = self.get
        return all(selfget(k, _MISS) == v for (k, v) in iteritems(other))

    # The following methods are mutating and so are not public. But they are implemented in this
    # non-mutable base class (rather than the mutable `bidict` subclass) because they are used here
    # during initialization (starting with the `_update` method). (Why is this? Because `__init__`
    # and `update` share a lot of the same behavior (inserting the provided items while respecting
    # the active duplication policies), so it makes sense for them to share implementation too.)
    def _pop(self, key):
        val = self._fwdm.pop(key)
        del self._invm[val]
        return val

    def _put(self, key, val, on_dup):
        dedup_result = self._dedup_item(key, val, on_dup)
        if dedup_result is not _NOOP:
            self._write_item(key, val, dedup_result)

    def _dedup_item(self, key, val, on_dup):
        """
        Check *key* and *val* for any duplication in self.

        Handle any duplication as per the duplication policies given in *on_dup*.

        (key, val) already present is construed as a no-op, not a duplication.

        If duplication is found and the corresponding duplication policy is
        :attr:`~bidict.RAISE`, raise the appropriate error.

        If duplication is found and the corresponding duplication policy is
        :attr:`~bidict.IGNORE`, return *None*.

        If duplication is found and the corresponding duplication policy is
        :attr:`~bidict.OVERWRITE`,
        or if no duplication is found,
        return the _DedupResult *(isdupkey, isdupval, oldkey, oldval)*.
        """
        fwdm = self._fwdm
        invm = self._invm
        oldval = fwdm.get(key, _MISS)
        oldkey = invm.get(val, _MISS)
        isdupkey = oldval is not _MISS
        isdupval = oldkey is not _MISS
        dedup_result = _DedupResult(isdupkey, isdupval, oldkey, oldval)
        if isdupkey and isdupval:
            if self._isdupitem(key, val, dedup_result):
                # (key, val) duplicates an existing item -> no-op.
                return _NOOP
            # key and val each duplicate a different existing item.
            if on_dup.kv is RAISE:
                raise KeyAndValueDuplicationError(key, val)
            elif on_dup.kv is IGNORE:
                return _NOOP
            assert on_dup.kv is OVERWRITE, 'invalid on_dup_kv: %r' % on_dup.kv
            # Fall through to the return statement on the last line.
        elif isdupkey:
            if on_dup.key is RAISE:
                raise KeyDuplicationError(key)
            elif on_dup.key is IGNORE:
                return _NOOP
            assert on_dup.key is OVERWRITE, 'invalid on_dup.key: %r' % on_dup.key
            # Fall through to the return statement on the last line.
        elif isdupval:
            if on_dup.val is RAISE:
                raise ValueDuplicationError(val)
            elif on_dup.val is IGNORE:
                return _NOOP
            assert on_dup.val is OVERWRITE, 'invalid on_dup.val: %r' % on_dup.val
            # Fall through to the return statement on the last line.
        # else neither isdupkey nor isdupval.
        return dedup_result

    @staticmethod
    def _isdupitem(key, val, dedup_result):
        isdupkey, isdupval, oldkey, oldval = dedup_result
        isdupitem = oldkey == key
        assert isdupitem == (oldval == val), '%r %r %r' % (key, val, dedup_result)
        if isdupitem:
            assert isdupkey
            assert isdupval
        return isdupitem

    @classmethod
    def _get_on_dup(cls, on_dup=None):
        if on_dup is None:
            on_dup = _OnDup(cls.on_dup_key, cls.on_dup_val, cls.on_dup_kv)
        elif not isinstance(on_dup, _OnDup):
            on_dup = _OnDup(*on_dup)
        if on_dup.kv is None:
            on_dup = on_dup._replace(kv=on_dup.val)
        return on_dup

    def _write_item(self, key, val, dedup_result):
        isdupkey, isdupval, oldkey, oldval = dedup_result
        fwdm = self._fwdm
        invm = self._invm
        fwdm[key] = val
        invm[val] = key
        if isdupkey:
            del invm[oldval]
        if isdupval:
            del fwdm[oldkey]
        return _WriteResult(key, val, oldkey, oldval)

    def _update(self, init, on_dup, *args, **kw):
        # args[0] may be a generator that yields many items, so process input in a single pass.
        if not args and not kw:
            return
        can_skip_dup_check = not self and not kw and isinstance(args[0], BidirectionalMapping)
        if can_skip_dup_check:
            self._update_no_dup_check(args[0])
            return
        on_dup = self._get_on_dup(on_dup)
        can_skip_rollback = init or RAISE not in on_dup
        if can_skip_rollback:
            self._update_no_rollback(on_dup, *args, **kw)
        else:
            self._update_with_rollback(on_dup, *args, **kw)

    def _update_no_dup_check(self, other, _nodup=_NODUP):
        write_item = self._write_item
        for (key, val) in iteritems(other):
            write_item(key, val, _nodup)

    def _update_no_rollback(self, on_dup, *args, **kw):
        put = self._put
        for (key, val) in _iteritems_args_kw(*args, **kw):
            put(key, val, on_dup)

    def _update_with_rollback(self, on_dup, *args, **kw):
        """Update, rolling back on failure."""
        writelog = []
        appendlog = writelog.append
        dedup_item = self._dedup_item
        write_item = self._write_item
        for (key, val) in _iteritems_args_kw(*args, **kw):
            try:
                dedup_result = dedup_item(key, val, on_dup)
            except DuplicationError:
                undo_write = self._undo_write
                for dedup_result, write_result in reversed(writelog):
                    undo_write(dedup_result, write_result)
                raise
            if dedup_result is not _NOOP:
                write_result = write_item(key, val, dedup_result)
                appendlog((dedup_result, write_result))

    def _undo_write(self, dedup_result, write_result):
        isdupkey, isdupval, _, _ = dedup_result
        key, val, oldkey, oldval = write_result
        if not isdupkey and not isdupval:
            self._pop(key)
            return
        fwdm = self._fwdm
        invm = self._invm
        if isdupkey:
            fwdm[key] = oldval
            invm[oldval] = key
            if not isdupval:
                del invm[val]
        if isdupval:
            invm[val] = oldkey
            fwdm[oldkey] = val
            if not isdupkey:
                del fwdm[key]

    def copy(self):
        """A shallow copy."""
        # Could just ``return self.__class__(self)`` here instead, but the below is faster. It uses
        # __new__ to create a copy instance while bypassing its __init__, which would result
        # in copying this bidict's items into the copy instance one at a time. Instead, make whole
        # copies of each of the backing mappings, and make them the backing mappings of the copy,
        # avoiding copying items one at a time.
        copy = self.__class__.__new__(self.__class__)
        copy._fwdm = self._fwdm.copy()  # pylint: disable=protected-access
        copy._invm = self._invm.copy()  # pylint: disable=protected-access
        copy._init_inv()  # pylint: disable=protected-access
        return copy

    def __copy__(self):
        """Used for the copy protocol.

        *See also* the :mod:`copy` module
        """
        return self.copy()

    def __len__(self):
        """The number of contained items."""
        return len(self._fwdm)

    def __iter__(self):  # lgtm [py/inheritance/incorrect-overridden-signature]
        """Iterator over the contained items."""
        # No default implementation for __iter__ inherited from Mapping ->
        # always delegate to _fwdm.
        return iter(self._fwdm)

    def __getitem__(self, key):
        u"""*x.__getitem__(key)　⟺　x[key]*"""
        return self._fwdm[key]

    def values(self):
        """A set-like object providing a view on the contained values.

        Note that because the values of a :class:`~bidict.BidirectionalMapping`
        are the keys of its inverse,
        this returns a :class:`~collections.abc.KeysView`
        rather than a :class:`~collections.abc.ValuesView`,
        which has the advantages of constant-time containment checks
        and supporting set operations.
        """
        return self.inverse.keys()

    if PY2:
        # For iterkeys and iteritems, inheriting from Mapping already provides
        # the best default implementations so no need to define here.

        def itervalues(self):
            """An iterator over the contained values."""
            return self.inverse.iterkeys()

        def viewkeys(self):  # noqa: D102; pylint: disable=missing-docstring
            return KeysView(self)

        def viewvalues(self):  # noqa: D102; pylint: disable=missing-docstring
            return self.inverse.viewkeys()

        viewvalues.__doc__ = values.__doc__
        values.__doc__ = 'A list of the contained values.'

        def viewitems(self):  # noqa: D102; pylint: disable=missing-docstring
            return ItemsView(self)

        # __ne__ added automatically in Python 3 when you implement __eq__, but not in Python 2.
        def __ne__(self, other):  # noqa: N802
            u"""*x.__ne__(other)　⟺　x != other*"""
            return not self == other  # Implement __ne__ in terms of __eq__.


#                             * Code review nav *
#==============================================================================
# ← Prev: _abc.py             Current: _base.py   Next: _delegating_mixins.py →
#==============================================================================
