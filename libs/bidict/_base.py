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
# ← Prev: _abc.py             Current: _base.py   Next:     _frozenbidict.py →
#==============================================================================


"""Provide :class:`BidictBase`."""

import typing as _t
from collections import namedtuple
from copy import copy
from weakref import ref

from ._abc import BidirectionalMapping
from ._dup import ON_DUP_DEFAULT, RAISE, DROP_OLD, DROP_NEW, OnDup
from ._exc import DuplicationError, KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError
from ._iter import _iteritems_args_kw
from ._typing import _NONE, KT, VT, OKT, OVT, IterItems, MapOrIterItems


_WriteResult = namedtuple('_WriteResult', 'key val oldkey oldval')
_DedupResult = namedtuple('_DedupResult', 'isdupkey isdupval invbyval fwdbykey')
_NODUP = _DedupResult(False, False, _NONE, _NONE)

BT = _t.TypeVar('BT', bound='BidictBase')  # typevar for BidictBase.copy


class BidictBase(BidirectionalMapping[KT, VT]):
    """Base class implementing :class:`BidirectionalMapping`."""

    __slots__ = ['_fwdm', '_invm', '_inv', '_invweak', '_hash', '__weakref__']

    #: The default :class:`~bidict.OnDup`
    #: that governs behavior when a provided item
    #: duplicates the key or value of other item(s).
    #:
    #: *See also* :ref:`basic-usage:Values Must Be Unique`, :doc:`extending`
    on_dup = ON_DUP_DEFAULT

    _fwdm_cls = dict  #: class of the backing forward mapping
    _invm_cls = dict  #: class of the backing inverse mapping

    #: The object used by :meth:`__repr__` for printing the contained items.
    _repr_delegate = dict

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        # Compute and set _inv_cls, the inverse of this bidict class.
        if '_inv_cls' in cls.__dict__:
            return
        if cls._fwdm_cls is cls._invm_cls:
            cls._inv_cls = cls
            return
        inv_cls = type(cls.__name__ + 'Inv', cls.__bases__, {
            **cls.__dict__,
            '_inv_cls': cls,
            '_fwdm_cls': cls._invm_cls,
            '_invm_cls': cls._fwdm_cls,
        })
        cls._inv_cls = inv_cls

    @_t.overload
    def __init__(self, __arg: _t.Mapping[KT, VT], **kw: VT) -> None: ...
    @_t.overload
    def __init__(self, __arg: IterItems[KT, VT], **kw: VT) -> None: ...
    @_t.overload
    def __init__(self, **kw: VT) -> None: ...
    def __init__(self, *args: MapOrIterItems[KT, VT], **kw: VT) -> None:
        """Make a new bidirectional dictionary.
        The signature behaves like that of :class:`dict`.
        Items passed in are added in the order they are passed,
        respecting the :attr:`on_dup` class attribute in the process.
        """
        #: The backing :class:`~collections.abc.Mapping`
        #: storing the forward mapping data (*key* → *value*).
        self._fwdm: _t.Dict[KT, VT] = self._fwdm_cls()
        #: The backing :class:`~collections.abc.Mapping`
        #: storing the inverse mapping data (*value* → *key*).
        self._invm: _t.Dict[VT, KT] = self._invm_cls()
        self._init_inv()
        if args or kw:
            self._update(True, self.on_dup, *args, **kw)

    def _init_inv(self) -> None:
        # Create the inverse bidict instance via __new__, bypassing its __init__ so that its
        # _fwdm and _invm can be assigned to this bidict's _invm and _fwdm. Store it in self._inv,
        # which holds a strong reference to a bidict's inverse, if one is available.
        self._inv = inv = self._inv_cls.__new__(self._inv_cls)  # type: ignore
        inv._fwdm = self._invm
        inv._invm = self._fwdm
        # Only give the inverse a weak reference to this bidict to avoid creating a reference cycle,
        # stored in the _invweak attribute. See also the docs in
        # :ref:`addendum:Bidict Avoids Reference Cycles`
        inv._inv = None
        inv._invweak = ref(self)
        # Since this bidict has a strong reference to its inverse already, set its _invweak to None.
        self._invweak = None

    @property
    def _isinv(self) -> bool:
        return self._inv is None

    @property
    def inverse(self) -> 'BidictBase[VT, KT]':
        """The inverse of this bidict."""
        # Resolve and return a strong reference to the inverse bidict.
        # One may be stored in self._inv already.
        if self._inv is not None:
            return self._inv  # type: ignore
        # Otherwise a weakref is stored in self._invweak. Try to get a strong ref from it.
        assert self._invweak is not None
        inv = self._invweak()
        if inv is not None:
            return inv
        # Refcount of referent must have dropped to zero, as in `bidict().inv.inv`. Init a new one.
        self._init_inv()  # Now this bidict will retain a strong ref to its inverse.
        return self._inv

    #: Alias for :attr:`inverse`.
    inv = inverse

    def __getstate__(self) -> dict:
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

    def __setstate__(self, state: dict) -> None:
        """Implemented because use of :attr:`__slots__` would prevent unpickling otherwise.

        *See also* :meth:`object.__setstate__`
        """
        for slot, value in state.items():
            setattr(self, slot, value)
        self._init_inv()

    def __repr__(self) -> str:
        """See :func:`repr`."""
        clsname = self.__class__.__name__
        if not self:
            return f'{clsname}()'
        return f'{clsname}({self._repr_delegate(self.items())})'

    # The inherited Mapping.__eq__ implementation would work, but it's implemented in terms of an
    # inefficient ``dict(self.items()) == dict(other.items())`` comparison, so override it with a
    # more efficient implementation.
    def __eq__(self, other: object) -> bool:
        """*x.__eq__(other)　⟺　x == other*

        Equivalent to *dict(x.items()) == dict(other.items())*
        but more efficient.

        Note that :meth:`bidict's __eq__() <bidict.bidict.__eq__>` implementation
        is inherited by subclasses,
        in particular by the ordered bidict subclasses,
        so even with ordered bidicts,
        :ref:`== comparison is order-insensitive <eq-order-insensitive>`.

        *See also* :meth:`bidict.FrozenOrderedBidict.equals_order_sensitive`
        """
        if not isinstance(other, _t.Mapping) or len(self) != len(other):
            return False
        selfget = self.get
        return all(selfget(k, _NONE) == v for (k, v) in other.items())  # type: ignore

    # The following methods are mutating and so are not public. But they are implemented in this
    # non-mutable base class (rather than the mutable `bidict` subclass) because they are used here
    # during initialization (starting with the `_update` method). (Why is this? Because `__init__`
    # and `update` share a lot of the same behavior (inserting the provided items while respecting
    # `on_dup`), so it makes sense for them to share implementation too.)
    def _pop(self, key: KT) -> VT:
        val = self._fwdm.pop(key)
        del self._invm[val]
        return val

    def _put(self, key: KT, val: VT, on_dup: OnDup) -> None:
        dedup_result = self._dedup_item(key, val, on_dup)
        if dedup_result is not None:
            self._write_item(key, val, dedup_result)

    def _dedup_item(self, key: KT, val: VT, on_dup: OnDup) -> _t.Optional[_DedupResult]:
        """Check *key* and *val* for any duplication in self.

        Handle any duplication as per the passed in *on_dup*.

        (key, val) already present is construed as a no-op, not a duplication.

        If duplication is found and the corresponding :class:`~bidict.OnDupAction` is
        :attr:`~bidict.DROP_NEW`, return None.

        If duplication is found and the corresponding :class:`~bidict.OnDupAction` is
        :attr:`~bidict.RAISE`, raise the appropriate error.

        If duplication is found and the corresponding :class:`~bidict.OnDupAction` is
        :attr:`~bidict.DROP_OLD`,
        or if no duplication is found,
        return the :class:`_DedupResult` *(isdupkey, isdupval, oldkey, oldval)*.
        """
        fwdm = self._fwdm
        invm = self._invm
        oldval: OVT = fwdm.get(key, _NONE)
        oldkey: OKT = invm.get(val, _NONE)
        isdupkey = oldval is not _NONE
        isdupval = oldkey is not _NONE
        dedup_result = _DedupResult(isdupkey, isdupval, oldkey, oldval)
        if isdupkey and isdupval:
            if self._already_have(key, val, oldkey, oldval):
                # (key, val) duplicates an existing item -> no-op.
                return None
            # key and val each duplicate a different existing item.
            if on_dup.kv is RAISE:
                raise KeyAndValueDuplicationError(key, val)
            if on_dup.kv is DROP_NEW:
                return None
            assert on_dup.kv is DROP_OLD
            # Fall through to the return statement on the last line.
        elif isdupkey:
            if on_dup.key is RAISE:
                raise KeyDuplicationError(key)
            if on_dup.key is DROP_NEW:
                return None
            assert on_dup.key is DROP_OLD
            # Fall through to the return statement on the last line.
        elif isdupval:
            if on_dup.val is RAISE:
                raise ValueDuplicationError(val)
            if on_dup.val is DROP_NEW:
                return None
            assert on_dup.val is DROP_OLD
            # Fall through to the return statement on the last line.
        # else neither isdupkey nor isdupval.
        return dedup_result

    @staticmethod
    def _already_have(key: KT, val: VT, oldkey: OKT, oldval: OVT) -> bool:
        # Overridden by _orderedbase.OrderedBidictBase.
        isdup = oldkey == key
        assert isdup == (oldval == val), f'{key} {val} {oldkey} {oldval}'
        return isdup

    def _write_item(self, key: KT, val: VT, dedup_result: _DedupResult) -> _WriteResult:
        # Overridden by _orderedbase.OrderedBidictBase.
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

    def _update(self, init: bool, on_dup: OnDup, *args: MapOrIterItems[KT, VT], **kw: VT) -> None:
        # args[0] may be a generator that yields many items, so process input in a single pass.
        if not args and not kw:
            return
        can_skip_dup_check = not self and not kw and isinstance(args[0], BidirectionalMapping)
        if can_skip_dup_check:
            self._update_no_dup_check(args[0])  # type: ignore
            return
        can_skip_rollback = init or RAISE not in on_dup
        if can_skip_rollback:
            self._update_no_rollback(on_dup, *args, **kw)
        else:
            self._update_with_rollback(on_dup, *args, **kw)

    def _update_no_dup_check(self, other: BidirectionalMapping[KT, VT]) -> None:
        write_item = self._write_item
        for (key, val) in other.items():
            write_item(key, val, _NODUP)

    def _update_no_rollback(self, on_dup: OnDup, *args: MapOrIterItems[KT, VT], **kw: VT) -> None:
        put = self._put
        for (key, val) in _iteritems_args_kw(*args, **kw):
            put(key, val, on_dup)

    def _update_with_rollback(self, on_dup: OnDup, *args: MapOrIterItems[KT, VT], **kw: VT) -> None:
        """Update, rolling back on failure."""
        writes: _t.List[_t.Tuple[_DedupResult, _WriteResult]] = []
        append_write = writes.append
        dedup_item = self._dedup_item
        write_item = self._write_item
        for (key, val) in _iteritems_args_kw(*args, **kw):
            try:
                dedup_result = dedup_item(key, val, on_dup)
            except DuplicationError:
                undo_write = self._undo_write
                for dedup_result, write_result in reversed(writes):
                    undo_write(dedup_result, write_result)
                raise
            if dedup_result is not None:
                write_result = write_item(key, val, dedup_result)
                append_write((dedup_result, write_result))

    def _undo_write(self, dedup_result: _DedupResult, write_result: _WriteResult) -> None:
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

    def copy(self: BT) -> BT:
        """A shallow copy."""
        # Could just ``return self.__class__(self)`` here instead, but the below is faster. It uses
        # __new__ to create a copy instance while bypassing its __init__, which would result
        # in copying this bidict's items into the copy instance one at a time. Instead, make whole
        # copies of each of the backing mappings, and make them the backing mappings of the copy,
        # avoiding copying items one at a time.
        cp = self.__class__.__new__(self.__class__)
        cp._fwdm = copy(self._fwdm)
        cp._invm = copy(self._invm)
        cp._init_inv()
        return cp  # type: ignore

    #: Used for the copy protocol.
    #: *See also* the :mod:`copy` module
    __copy__ = copy

    def __len__(self) -> int:
        """The number of contained items."""
        return len(self._fwdm)

    def __iter__(self) -> _t.Iterator[KT]:
        """Iterator over the contained keys."""
        return iter(self._fwdm)

    def __getitem__(self, key: KT) -> VT:
        """*x.__getitem__(key)　⟺　x[key]*"""
        return self._fwdm[key]


# Work around weakref slot with Generics bug on Python 3.6 (https://bugs.python.org/issue41451):
BidictBase.__slots__.remove('__weakref__')

#                             * Code review nav *
#==============================================================================
# ← Prev: _abc.py             Current: _base.py   Next:     _frozenbidict.py →
#==============================================================================
