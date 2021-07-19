# -*- coding: utf-8 -*-
# Copyright 2009-2019 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Provides :func:`bidict.namedbidict`."""

import re

from ._abc import BidirectionalMapping
from ._bidict import bidict
from .compat import PY2


_isidentifier = (  # pylint: disable=invalid-name
    re.compile('[A-Za-z_][A-Za-z0-9_]*$').match if PY2 else str.isidentifier
)


def namedbidict(typename, keyname, valname, base_type=bidict):
    r"""Create a new subclass of *base_type* with custom accessors.

    Analagous to :func:`collections.namedtuple`.

    The new class's ``__name__`` and ``__qualname__``
    will be set based on *typename*.

    Instances of it will provide access to their
    :attr:`inverse <BidirectionalMapping.inverse>`\s
    via the custom *keyname*\_for property,
    and access to themselves
    via the custom *valname*\_for property.

    *See also* the :ref:`namedbidict usage documentation
    <other-bidict-types:\:func\:\`~bidict.namedbidict\`>`

    :raises ValueError: if any of the *typename*, *keyname*, or *valname*
        strings is not a valid Python identifier, or if *keyname == valname*.

    :raises TypeError: if *base_type* is not a subclass of
        :class:`BidirectionalMapping`.
        (This function requires slightly more of *base_type*,
        e.g. the availability of an ``_isinv`` attribute,
        but all the :ref:`concrete bidict types
        <other-bidict-types:Bidict Types Diagram>`
        that the :mod:`bidict` module provides can be passed in.
        Check out the code if you actually need to pass in something else.)
    """
    # Re the `base_type` docs above:
    # The additional requirements (providing _isinv and __getstate__) do not belong in the
    # BidirectionalMapping interface, and it's overkill to create additional interface(s) for this.
    # On the other hand, it's overkill to require that base_type be a subclass of BidictBase, since
    # that's too specific. The BidirectionalMapping check along with the docs above should suffice.
    if not issubclass(base_type, BidirectionalMapping):
        raise TypeError(base_type)
    names = (typename, keyname, valname)
    if not all(map(_isidentifier, names)) or keyname == valname:
        raise ValueError(names)

    class _Named(base_type):  # pylint: disable=too-many-ancestors

        __slots__ = ()

        def _getfwd(self):
            return self.inverse if self._isinv else self

        def _getinv(self):
            return self if self._isinv else self.inverse

        @property
        def _keyname(self):
            return valname if self._isinv else keyname

        @property
        def _valname(self):
            return keyname if self._isinv else valname

        def __reduce__(self):
            return (_make_empty, (typename, keyname, valname, base_type), self.__getstate__())

    bname = base_type.__name__
    fname = valname + '_for'
    iname = keyname + '_for'
    names = dict(typename=typename, bname=bname, keyname=keyname, valname=valname)
    fdoc = u'{typename} forward {bname}: {keyname} → {valname}'.format(**names)
    idoc = u'{typename} inverse {bname}: {valname} → {keyname}'.format(**names)
    setattr(_Named, fname, property(_Named._getfwd, doc=fdoc))  # pylint: disable=protected-access
    setattr(_Named, iname, property(_Named._getinv, doc=idoc))  # pylint: disable=protected-access

    if not PY2:
        _Named.__qualname__ = _Named.__qualname__[:-len(_Named.__name__)] + typename
    _Named.__name__ = typename
    return _Named


def _make_empty(typename, keyname, valname, base_type):
    """Create a named bidict with the indicated arguments and return an empty instance.
    Used to make :func:`bidict.namedbidict` instances picklable.
    """
    cls = namedbidict(typename, keyname, valname, base_type=base_type)
    return cls()
