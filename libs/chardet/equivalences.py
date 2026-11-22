"""Backward-compatibility shim for ``chardet.equivalences``.

This module's contents were split in chardet 7.5: accuracy-evaluation tables
and predicates moved to :mod:`chardet.evaluation`, and public-API encoding-name
remapping moved to :mod:`chardet.output_names`.  This module proxies every
attribute to whichever of those two now owns it, so existing callers keep
working.

.. deprecated:: 7.5
    Import from :mod:`chardet.evaluation` (``is_correct``,
    ``is_equivalent_detection``, ``is_language_equivalent``, ``SUPERSETS``,
    ``BIDIRECTIONAL_GROUPS``, ``LANGUAGE_EQUIVALENCES``) or
    :mod:`chardet.output_names` (``apply_compat_names``,
    ``apply_preferred_superset``, ``apply_legacy_rename``,
    ``PREFERRED_SUPERSET``) instead.
    Will be removed in chardet 8.0.
"""

from __future__ import annotations

import sys
import warnings
from types import ModuleType
from typing import Any

from chardet import evaluation, output_names

#: Modules that now own the names this one used to define, searched in order.
#: Every name the pre-split module exposed lives in one of them --- including
#: the private helpers (``_chars_equivalent``, ``_remap_encoding``, the
#: normalized lookup tables) and the imported-module names (``unicodedata``,
#: ``lookup_encoding``) that leaked into the old namespace.
_SOURCES: tuple[ModuleType, ...] = (evaluation, output_names)

#: The documented surface, for ``from chardet.equivalences import *``.  None
#: of these names is defined here --- they resolve through the proxy below,
#: which is also why ``__all__`` is built rather than written as a literal:
#: a literal is checked against the module's own bindings, and every entry
#: would read as undefined.
_PUBLIC_NAMES = (
    "BIDIRECTIONAL_GROUPS",
    "LANGUAGE_EQUIVALENCES",
    "PREFERRED_SUPERSET",
    "SUPERSETS",
    "apply_compat_names",
    "apply_legacy_rename",
    "apply_preferred_superset",
    "is_correct",
    "is_equivalent_detection",
    "is_language_equivalent",
)

__all__ = list(_PUBLIC_NAMES)


#: Which module owns each name the pre-split module exposed, fixed at
#: import.  Ownership is a fact about the split, not about what happens to
#: be bound at lookup time: looking it up live would let a deletion strand
#: the name, since the re-set that follows would find no owner and land on
#: this module instead.  That delete-then-set is exactly the round trip
#: ``unittest.mock.patch.object`` performs on exit.
_OWNERS: dict[str, ModuleType] = {}
for _source in _SOURCES:
    for _name in vars(_source):
        if not (_name.startswith("__") and _name.endswith("__")):
            _OWNERS.setdefault(_name, _source)
del _source, _name


def _owner(name: str) -> ModuleType | None:
    """Return the module that now owns *name*, or ``None`` if neither does.

    Dunders are never proxied: every module carries ``__spec__``,
    ``__name__`` and friends, and the import system assigns them on this
    module directly (``importlib.reload`` does exactly that), which without
    this guard would overwrite the owning module's own.
    """
    return _OWNERS.get(name)


def _warn(name: str, owner: ModuleType) -> None:
    """Emit the deprecation warning for one accessed name."""
    warnings.warn(
        f"chardet.equivalences is deprecated; import {name} from "
        f"{owner.__name__} instead. Will be removed in chardet 8.0.",
        DeprecationWarning,
        # _warn -> __getattr__/__setattr__ -> the caller being warned about.
        stacklevel=3,
    )


class _EquivalencesShim(ModuleType):
    """Module type that proxies attributes to the module that now owns them.

    Proxying rather than re-exporting by value preserves two properties the
    pre-split module had.  Reads, writes, and deletes stay indirected:
    rebinding ``chardet.equivalences.PREFERRED_SUPERSET`` rebinds the table
    :func:`~chardet.output_names.apply_preferred_superset` actually reads, so
    a monkeypatching caller is not silently ignored, and a
    ``unittest.mock.patch.object`` on this module patches the owner and
    restores it on exit.  And the deprecation
    fires per accessed name, naming both the name and its new home, instead
    of once per process at import time --- which attributed the warning to
    whoever imported first, said nothing about which symbol was deprecated,
    and turned ``import chardet.equivalences`` into a hard error under
    ``-W error::DeprecationWarning``.
    """

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        owner = _owner(name)
        if owner is None:
            msg = f"module {__name__!r} has no attribute {name!r}"
            raise AttributeError(msg)
        _warn(name, owner)
        return getattr(owner, name)

    def __setattr__(self, name: str, value: Any) -> None:  # noqa: ANN401
        owner = _owner(name)
        if owner is None:
            super().__setattr__(name, value)
            return
        _warn(name, owner)
        setattr(owner, name, value)

    def __delattr__(self, name: str) -> None:
        owner = _owner(name)
        if owner is None:
            super().__delattr__(name)
            return
        _warn(name, owner)
        delattr(owner, name)

    def __dir__(self) -> list[str]:
        names = set(super().__dir__())
        for source in _SOURCES:
            names.update(vars(source))
        return sorted(names)


# Swapping the class is what buys the write-through above: PEP 562's
# module-level ``__getattr__`` intercepts reads only.
sys.modules[__name__].__class__ = _EquivalencesShim
