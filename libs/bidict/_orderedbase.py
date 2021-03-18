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
# ← Prev: _bidict.py       Current: _orderedbase.py   Next: _frozenordered.py →
#==============================================================================


"""Provide :class:`OrderedBidictBase`."""

import typing as _t
from copy import copy
from weakref import ref

from ._base import _NONE, _DedupResult, _WriteResult, BidictBase, BT
from ._bidict import bidict
from ._typing import KT, VT, IterItems, MapOrIterItems


class _Node:
    """A node in a circular doubly-linked list
    used to encode the order of items in an ordered bidict.

    Only weak references to the next and previous nodes
    are held to avoid creating strong reference cycles.

    Because an ordered bidict retains two strong references
    to each node instance (one from its backing `_fwdm` mapping
    and one from its `_invm` mapping), a node's refcount will not
    drop to zero (and so will not be garbage collected) as long as
    the ordered bidict that contains it is still alive.
    Because nodes don't have strong reference cycles,
    once their containing bidict is freed,
    they too are immediately freed.
    """

    __slots__ = ('_prv', '_nxt', '__weakref__')

    def __init__(self, prv: '_Node' = None, nxt: '_Node' = None) -> None:
        self._setprv(prv)
        self._setnxt(nxt)

    def __repr__(self) -> str:
        clsname = self.__class__.__name__
        prv = id(self.prv)
        nxt = id(self.nxt)
        return f'{clsname}(prv={prv}, self={id(self)}, nxt={nxt})'

    def _getprv(self) -> '_t.Optional[_Node]':
        return self._prv() if isinstance(self._prv, ref) else self._prv

    def _setprv(self, prv: '_t.Optional[_Node]') -> None:
        self._prv = prv and ref(prv)

    prv = property(_getprv, _setprv)

    def _getnxt(self) -> '_t.Optional[_Node]':
        return self._nxt() if isinstance(self._nxt, ref) else self._nxt

    def _setnxt(self, nxt: '_t.Optional[_Node]') -> None:
        self._nxt = nxt and ref(nxt)

    nxt = property(_getnxt, _setnxt)

    def __getstate__(self) -> dict:
        """Return the instance state dictionary
        but with weakrefs converted to strong refs
        so that it can be pickled.

        *See also* :meth:`object.__getstate__`
        """
        return dict(_prv=self.prv, _nxt=self.nxt)

    def __setstate__(self, state: dict) -> None:
        """Set the instance state from *state*."""
        self._setprv(state['_prv'])
        self._setnxt(state['_nxt'])


class _SentinelNode(_Node):
    """Special node in a circular doubly-linked list
    that links the first node with the last node.
    When its next and previous references point back to itself
    it represents an empty list.
    """

    __slots__ = ()

    def __init__(self, prv: _Node = None, nxt: _Node = None) -> None:
        super().__init__(prv or self, nxt or self)

    def __repr__(self) -> str:
        return '<SNTL>'

    def __bool__(self) -> bool:
        return False

    def _iter(self, *, reverse: bool = False) -> _t.Iterator[_Node]:
        """Iterator yielding nodes in the requested order,
        i.e. traverse the linked list via :attr:`nxt`
        (or :attr:`prv` if *reverse* is truthy)
        until reaching a falsy (i.e. sentinel) node.
        """
        attr = 'prv' if reverse else 'nxt'
        node = getattr(self, attr)
        while node:
            yield node
            node = getattr(node, attr)


class OrderedBidictBase(BidictBase[KT, VT]):
    """Base class implementing an ordered :class:`BidirectionalMapping`."""

    __slots__ = ('_sntl',)

    _fwdm_cls = bidict  # type: ignore
    _invm_cls = bidict  # type: ignore

    #: The object used by :meth:`__repr__` for printing the contained items.
    _repr_delegate = list  # type: ignore

    @_t.overload
    def __init__(self, __arg: _t.Mapping[KT, VT], **kw: VT) -> None: ...
    @_t.overload
    def __init__(self, __arg: IterItems[KT, VT], **kw: VT) -> None: ...
    @_t.overload
    def __init__(self, **kw: VT) -> None: ...
    def __init__(self, *args: MapOrIterItems[KT, VT], **kw: VT) -> None:
        """Make a new ordered bidirectional mapping.
        The signature behaves like that of :class:`dict`.
        Items passed in are added in the order they are passed,
        respecting the :attr:`on_dup` class attribute in the process.

        The order in which items are inserted is remembered,
        similar to :class:`collections.OrderedDict`.
        """
        self._sntl = _SentinelNode()

        # Like unordered bidicts, ordered bidicts also store two backing one-directional mappings
        # `_fwdm` and `_invm`. But rather than mapping `key` to `val` and `val` to `key`
        # (respectively), they map `key` to `nodefwd` and `val` to `nodeinv` (respectively), where
        # `nodefwd` is `nodeinv` when `key` and `val` are associated with one another.

        # To effect this difference, `_write_item` and `_undo_write` are overridden. But much of the
        # rest of BidictBase's implementation, including BidictBase.__init__ and BidictBase._update,
        # are inherited and are able to be reused without modification.
        super().__init__(*args, **kw)

    if _t.TYPE_CHECKING:
        @property
        def inverse(self) -> 'OrderedBidictBase[VT, KT]': ...
        _fwdm: bidict[KT, _Node]  # type: ignore
        _invm: bidict[VT, _Node]  # type: ignore

    def _init_inv(self) -> None:
        super()._init_inv()
        self.inverse._sntl = self._sntl

    # Can't reuse BidictBase.copy since ordered bidicts have different internal structure.
    def copy(self: BT) -> BT:
        """A shallow copy of this ordered bidict."""
        # Fast copy implementation bypassing __init__. See comments in :meth:`BidictBase.copy`.
        cp = self.__class__.__new__(self.__class__)
        sntl = _SentinelNode()
        fwdm = copy(self._fwdm)
        invm = copy(self._invm)
        cur = sntl
        nxt = sntl.nxt
        for (key, val) in self.items():
            nxt = _Node(cur, sntl)
            cur.nxt = fwdm[key] = invm[val] = nxt
            cur = nxt
        sntl.prv = nxt
        cp._sntl = sntl
        cp._fwdm = fwdm
        cp._invm = invm
        cp._init_inv()
        return cp  # type: ignore

    __copy__ = copy

    def __getitem__(self, key: KT) -> VT:
        nodefwd = self._fwdm[key]
        val = self._invm.inverse[nodefwd]
        return val

    def _pop(self, key: KT) -> VT:
        nodefwd = self._fwdm.pop(key)
        val = self._invm.inverse.pop(nodefwd)
        nodefwd.prv.nxt = nodefwd.nxt
        nodefwd.nxt.prv = nodefwd.prv
        return val

    @staticmethod
    def _already_have(key: KT, val: VT, nodeinv: _Node, nodefwd: _Node) -> bool:  # type: ignore
        # Overrides _base.BidictBase.
        return nodeinv is nodefwd

    def _write_item(self, key: KT, val: VT, dedup_result: _DedupResult) -> _WriteResult:
        # Overrides _base.BidictBase.
        fwdm = self._fwdm  # bidict mapping keys to nodes
        invm = self._invm  # bidict mapping vals to nodes
        isdupkey, isdupval, nodeinv, nodefwd = dedup_result
        if not isdupkey and not isdupval:
            # No key or value duplication -> create and append a new node.
            sntl = self._sntl
            last = sntl.prv
            node = _Node(last, sntl)
            last.nxt = sntl.prv = fwdm[key] = invm[val] = node
            oldkey = oldval = _NONE
        elif isdupkey and isdupval:
            # Key and value duplication across two different nodes.
            assert nodefwd is not nodeinv
            oldval = invm.inverse[nodefwd]  # type: ignore
            oldkey = fwdm.inverse[nodeinv]  # type: ignore
            assert oldkey != key
            assert oldval != val
            # We have to collapse nodefwd and nodeinv into a single node, i.e. drop one of them.
            # Drop nodeinv, so that the item with the same key is the one overwritten in place.
            nodeinv.prv.nxt = nodeinv.nxt
            nodeinv.nxt.prv = nodeinv.prv
            # Don't remove nodeinv's references to its neighbors since
            # if the update fails, we'll need them to undo this write.
            # Update fwdm and invm.
            tmp = fwdm.pop(oldkey)  # type: ignore
            assert tmp is nodeinv
            tmp = invm.pop(oldval)  # type: ignore
            assert tmp is nodefwd
            fwdm[key] = invm[val] = nodefwd
        elif isdupkey:
            oldval = invm.inverse[nodefwd]  # type: ignore
            oldkey = _NONE
            oldnodeinv = invm.pop(oldval)  # type: ignore
            assert oldnodeinv is nodefwd
            invm[val] = nodefwd
        else:  # isdupval
            oldkey = fwdm.inverse[nodeinv]  # type: ignore
            oldval = _NONE
            oldnodefwd = fwdm.pop(oldkey)  # type: ignore
            assert oldnodefwd is nodeinv
            fwdm[key] = nodeinv
        return _WriteResult(key, val, oldkey, oldval)

    def _undo_write(self, dedup_result: _DedupResult, write_result: _WriteResult) -> None:
        fwdm = self._fwdm
        invm = self._invm
        isdupkey, isdupval, nodeinv, nodefwd = dedup_result
        key, val, oldkey, oldval = write_result
        if not isdupkey and not isdupval:
            self._pop(key)
        elif isdupkey and isdupval:
            # Restore original items.
            nodeinv.prv.nxt = nodeinv.nxt.prv = nodeinv
            fwdm[oldkey] = invm[val] = nodeinv
            invm[oldval] = fwdm[key] = nodefwd
        elif isdupkey:
            tmp = invm.pop(val)
            assert tmp is nodefwd
            invm[oldval] = nodefwd
            assert fwdm[key] is nodefwd
        else:  # isdupval
            tmp = fwdm.pop(key)
            assert tmp is nodeinv
            fwdm[oldkey] = nodeinv
            assert invm[val] is nodeinv

    def __iter__(self) -> _t.Iterator[KT]:
        """Iterator over the contained keys in insertion order."""
        return self._iter()

    def _iter(self, *, reverse: bool = False) -> _t.Iterator[KT]:
        fwdm_inv = self._fwdm.inverse
        for node in self._sntl._iter(reverse=reverse):
            yield fwdm_inv[node]

    def __reversed__(self) -> _t.Iterator[KT]:
        """Iterator over the contained keys in reverse insertion order."""
        yield from self._iter(reverse=True)

    def equals_order_sensitive(self, other: object) -> bool:
        """Order-sensitive equality check.

        *See also* :ref:`eq-order-insensitive`
        """
        # Same short-circuit as BidictBase.__eq__. Factoring out not worth function call overhead.
        if not isinstance(other, _t.Mapping) or len(self) != len(other):
            return False
        return all(i == j for (i, j) in zip(self.items(), other.items()))


#                             * Code review nav *
#==============================================================================
# ← Prev: _bidict.py       Current: _orderedbase.py   Next: _frozenordered.py →
#==============================================================================
