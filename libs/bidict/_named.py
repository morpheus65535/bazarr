# -*- coding: utf-8 -*-
# Copyright 2009-2021 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Provide :func:`bidict.namedbidict`."""

import typing as _t
from sys import _getframe

from ._abc import BidirectionalMapping, KT, VT
from ._bidict import bidict


def namedbidict(
    typename: str,
    keyname: str,
    valname: str,
    *,
    base_type: _t.Type[BidirectionalMapping[KT, VT]] = bidict,
) -> _t.Type[BidirectionalMapping[KT, VT]]:
    r"""Create a new subclass of *base_type* with custom accessors.

    Like :func:`collections.namedtuple` for bidicts.

    The new class's ``__name__`` and ``__qualname__`` will be set to *typename*,
    and its ``__module__`` will be set to the caller's module.

    Instances of the new class will provide access to their
    :attr:`inverse <BidirectionalMapping.inverse>` instances
    via the custom *keyname*\_for property,
    and access to themselves
    via the custom *valname*\_for property.

    *See also* the :ref:`namedbidict usage documentation
    <other-bidict-types:\:func\:\`~bidict.namedbidict\`>`

    :raises ValueError: if any of the *typename*, *keyname*, or *valname*
        strings is not a valid Python identifier, or if *keyname == valname*.

    :raises TypeError: if *base_type* is not a :class:`BidirectionalMapping` subclass
        that provides ``_isinv`` and :meth:`~object.__getstate__` attributes.
        (Any :class:`~bidict.BidictBase` subclass can be passed in, including all the
        concrete bidict types pictured in the :ref:`other-bidict-types:Bidict Types Diagram`.
    """
    if not issubclass(base_type, BidirectionalMapping) or not all(hasattr(base_type, i) for i in ('_isinv', '__getstate__')):
        raise TypeError(base_type)
    names = (typename, keyname, valname)
    if not all(map(str.isidentifier, names)) or keyname == valname:
        raise ValueError(names)

    class _Named(base_type):  # type: ignore [valid-type,misc]

        __slots__ = ()

        def _getfwd(self) -> '_Named':
            return self.inverse if self._isinv else self  # type: ignore [no-any-return]

        def _getinv(self) -> '_Named':
            return self if self._isinv else self.inverse  # type: ignore [no-any-return]

        @property
        def _keyname(self) -> str:
            return valname if self._isinv else keyname

        @property
        def _valname(self) -> str:
            return keyname if self._isinv else valname

        def __reduce__(self) -> '_t.Tuple[_t.Callable[[str, str, str, _t.Type[BidirectionalMapping]], BidirectionalMapping], _t.Tuple[str, str, str, _t.Type[BidirectionalMapping]], dict]':
            return (_make_empty, (typename, keyname, valname, base_type), self.__getstate__())

    bname = base_type.__name__
    fname = valname + '_for'
    iname = keyname + '_for'
    fdoc = f'{typename} forward {bname}: {keyname} → {valname}'
    idoc = f'{typename} inverse {bname}: {valname} → {keyname}'
    setattr(_Named, fname, property(_Named._getfwd, doc=fdoc))
    setattr(_Named, iname, property(_Named._getinv, doc=idoc))

    _Named.__name__ = typename
    _Named.__qualname__ = typename
    _Named.__module__ = _getframe(1).f_globals.get('__name__')  # type: ignore [assignment]
    return _Named


def _make_empty(
    typename: str,
    keyname: str,
    valname: str,
    base_type: _t.Type[BidirectionalMapping] = bidict,
) -> BidirectionalMapping:
    """Create a named bidict with the indicated arguments and return an empty instance.
    Used to make :func:`bidict.namedbidict` instances picklable.
    """
    cls = namedbidict(typename, keyname, valname, base_type=base_type)
    return cls()
