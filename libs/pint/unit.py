"""
    pint.unit
    ~~~~~~~~~

    Functions and classes related to unit definitions and conversions.

    :copyright: 2016 by Pint Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import copy
import locale
import operator
from numbers import Number

from .compat import NUMERIC_TYPES, is_upcast_type
from .definitions import UnitDefinition
from .errors import DimensionalityError
from .formatting import siunitx_format_unit
from .util import PrettyIPython, SharedRegistryObject, UnitsContainer


class Unit(PrettyIPython, SharedRegistryObject):
    """Implements a class to describe a unit supporting math operations."""

    #: Default formatting string.
    default_format = ""

    def __reduce__(self):
        # See notes in Quantity.__reduce__
        from . import _unpickle_unit

        return _unpickle_unit, (Unit, self._units)

    def __init__(self, units):
        super().__init__()
        if isinstance(units, (UnitsContainer, UnitDefinition)):
            self._units = units
        elif isinstance(units, str):
            self._units = self._REGISTRY.parse_units(units)._units
        elif isinstance(units, Unit):
            self._units = units._units
        else:
            raise TypeError(
                "units must be of type str, Unit or "
                "UnitsContainer; not {}.".format(type(units))
            )

        self.__used = False
        self.__handling = None

    @property
    def debug_used(self):
        return self.__used

    def __copy__(self):
        ret = self.__class__(self._units)
        ret.__used = self.__used
        return ret

    def __deepcopy__(self, memo):
        ret = self.__class__(copy.deepcopy(self._units, memo))
        ret.__used = self.__used
        return ret

    def __str__(self):
        return format(self)

    def __bytes__(self):
        return str(self).encode(locale.getpreferredencoding())

    def __repr__(self):
        return "<Unit('{}')>".format(self._units)

    def __format__(self, spec):
        spec = spec or self.default_format
        # special cases
        if "Lx" in spec:  # the LaTeX siunitx code
            return r"\si[]{%s}" % siunitx_format_unit(self)

        if "~" in spec:
            if not self._units:
                return ""
            units = UnitsContainer(
                dict(
                    (self._REGISTRY._get_symbol(key), value)
                    for key, value in self._units.items()
                )
            )
            spec = spec.replace("~", "")
        else:
            units = self._units

        return format(units, spec)

    def format_babel(self, spec="", **kwspec):
        spec = spec or self.default_format

        if "~" in spec:
            if self.dimensionless:
                return ""
            units = UnitsContainer(
                dict(
                    (self._REGISTRY._get_symbol(key), value)
                    for key, value in self._units.items()
                )
            )
            spec = spec.replace("~", "")
        else:
            units = self._units

        return "%s" % (units.format_babel(spec, **kwspec))

    @property
    def dimensionless(self):
        """Return True if the Unit is dimensionless; False otherwise.
        """
        return not bool(self.dimensionality)

    @property
    def dimensionality(self):
        """
        Returns
        -------
        dict
            Dimensionality of the Unit, e.g. ``{length: 1, time: -1}``
        """
        try:
            return self._dimensionality
        except AttributeError:
            dim = self._REGISTRY._get_dimensionality(self._units)
            self._dimensionality = dim

        return self._dimensionality

    def compatible_units(self, *contexts):
        if contexts:
            with self._REGISTRY.context(*contexts):
                return self._REGISTRY.get_compatible_units(self)

        return self._REGISTRY.get_compatible_units(self)

    def is_compatible_with(self, other, *contexts, **ctx_kwargs):
        """ check if the other object is compatible

        Parameters
        ----------
        other
            The object to check. Treated as dimensionless if not a
            Quantity, Unit or str.
        *contexts : str or pint.Context
            Contexts to use in the transformation.
        **ctx_kwargs :
            Values for the Context/s

        Returns
        -------
        bool
        """
        if contexts:
            try:
                (1 * self).to(other, *contexts, **ctx_kwargs)
                return True
            except DimensionalityError:
                return False

        if isinstance(other, (self._REGISTRY.Quantity, self._REGISTRY.Unit)):
            return self.dimensionality == other.dimensionality

        if isinstance(other, str):
            return (
                self.dimensionality == self._REGISTRY.parse_units(other).dimensionality
            )

        return self.dimensionless

    def __mul__(self, other):
        if self._check(other):
            if isinstance(other, self.__class__):
                return self.__class__(self._units * other._units)
            else:
                qself = self._REGISTRY.Quantity(1, self._units)
                return qself * other

        if isinstance(other, Number) and other == 1:
            return self._REGISTRY.Quantity(other, self._units)

        return self._REGISTRY.Quantity(1, self._units) * other

    __rmul__ = __mul__

    def __truediv__(self, other):
        if self._check(other):
            if isinstance(other, self.__class__):
                return self.__class__(self._units / other._units)
            else:
                qself = 1 * self
                return qself / other

        return self._REGISTRY.Quantity(1 / other, self._units)

    def __rtruediv__(self, other):
        # As Unit and Quantity both handle truediv with each other rtruediv can
        # only be called for something different.
        if isinstance(other, NUMERIC_TYPES):
            return self._REGISTRY.Quantity(other, 1 / self._units)
        elif isinstance(other, UnitsContainer):
            return self.__class__(other / self._units)
        else:
            return NotImplemented

    __div__ = __truediv__
    __rdiv__ = __rtruediv__

    def __pow__(self, other):
        if isinstance(other, NUMERIC_TYPES):
            return self.__class__(self._units ** other)

        else:
            mess = "Cannot power Unit by {}".format(type(other))
            raise TypeError(mess)

    def __hash__(self):
        return self._units.__hash__()

    def __eq__(self, other):
        # We compare to the base class of Unit because each Unit class is
        # unique.
        if self._check(other):
            if isinstance(other, self.__class__):
                return self._units == other._units
            else:
                return other == self._REGISTRY.Quantity(1, self._units)

        elif isinstance(other, NUMERIC_TYPES):
            return other == self._REGISTRY.Quantity(1, self._units)

        else:
            return self._units == other

    def __ne__(self, other):
        return not (self == other)

    def compare(self, other, op):
        self_q = self._REGISTRY.Quantity(1, self)

        if isinstance(other, NUMERIC_TYPES):
            return self_q.compare(other, op)
        elif isinstance(other, (Unit, UnitsContainer, dict)):
            return self_q.compare(self._REGISTRY.Quantity(1, other), op)
        else:
            return NotImplemented

    __lt__ = lambda self, other: self.compare(other, op=operator.lt)
    __le__ = lambda self, other: self.compare(other, op=operator.le)
    __ge__ = lambda self, other: self.compare(other, op=operator.ge)
    __gt__ = lambda self, other: self.compare(other, op=operator.gt)

    def __int__(self):
        return int(self._REGISTRY.Quantity(1, self._units))

    def __float__(self):
        return float(self._REGISTRY.Quantity(1, self._units))

    def __complex__(self):
        return complex(self._REGISTRY.Quantity(1, self._units))

    __array_priority__ = 17

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        if method != "__call__":
            # Only handle ufuncs as callables
            return NotImplemented

        # Check types and return NotImplemented when upcast type encountered
        types = set(
            type(arg)
            for arg in list(inputs) + list(kwargs.values())
            if hasattr(arg, "__array_ufunc__")
        )
        if any(is_upcast_type(other) for other in types):
            return NotImplemented

        # Act on limited implementations by conversion to multiplicative identity
        # Quantity
        if ufunc.__name__ in ("true_divide", "divide", "floor_divide", "multiply"):
            return ufunc(
                *tuple(
                    self._REGISTRY.Quantity(1, self._units) if arg is self else arg
                    for arg in inputs
                ),
                **kwargs,
            )
        else:
            return NotImplemented

    @property
    def systems(self):
        out = set()
        for uname in self._units.keys():
            for sname, sys in self._REGISTRY._systems.items():
                if uname in sys.members:
                    out.add(sname)
        return frozenset(out)

    def from_(self, value, strict=True, name="value"):
        """Converts a numerical value or quantity to this unit

        Parameters
        ----------
        value :
            a Quantity (or numerical value if strict=False) to convert
        strict :
            boolean to indicate that only quanities are accepted (Default value = True)
        name :
            descriptive name to use if an exception occurs (Default value = "value")

        Returns
        -------
        type
            The converted value as this unit

        """
        if self._check(value):
            if not isinstance(value, self._REGISTRY.Quantity):
                value = self._REGISTRY.Quantity(1, value)
            return value.to(self)
        elif strict:
            raise ValueError("%s must be a Quantity" % value)
        else:
            return value * self

    def m_from(self, value, strict=True, name="value"):
        """Converts a numerical value or quantity to this unit, then returns
        the magnitude of the converted value

        Parameters
        ----------
        value :
            a Quantity (or numerical value if strict=False) to convert
        strict :
            boolean to indicate that only quanities are accepted (Default value = True)
        name :
            descriptive name to use if an exception occurs (Default value = "value")

        Returns
        -------
        type
            The magnitude of the converted value

        """
        return self.from_(value, strict=strict, name=name).magnitude


_Unit = Unit


def build_unit_class(registry):
    class Unit(_Unit):
        _REGISTRY = registry

    return Unit
