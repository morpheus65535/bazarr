"""
    pint.quantity
    ~~~~~~~~~~~~~

    :copyright: 2016 by Pint Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import bisect
import contextlib
import copy
import datetime
import functools
import locale
import math
import numbers
import operator
import re
import warnings
from typing import List

from packaging import version

from .compat import (
    HAS_NUMPY_ARRAY_FUNCTION,
    NUMPY_VER,
    _to_magnitude,
    babel_parse,
    compute,
    dask_array,
    eq,
    is_duck_array_type,
    is_upcast_type,
    ndarray,
    np,
    persist,
    visualize,
    zero_or_nan,
)
from .definitions import UnitDefinition
from .errors import (
    DimensionalityError,
    OffsetUnitCalculusError,
    PintTypeError,
    UnitStrippedWarning,
)
from .formatting import (
    _pretty_fmt_exponent,
    ndarray_to_latex,
    remove_custom_flags,
    siunitx_format_unit,
)
from .numpy_func import (
    HANDLED_UFUNCS,
    copy_units_output_ufuncs,
    get_op_output_unit,
    matching_input_copy_units_output_ufuncs,
    matching_input_set_units_output_ufuncs,
    numpy_wrap,
    op_units_output_ufuncs,
    set_units_ufuncs,
)
from .util import (
    PrettyIPython,
    SharedRegistryObject,
    UnitsContainer,
    infer_base_unit,
    iterable,
    logger,
    to_units_container,
)


class _Exception(Exception):  # pragma: no cover
    def __init__(self, internal):
        self.internal = internal


def reduce_dimensions(f):
    def wrapped(self, *args, **kwargs):
        result = f(self, *args, **kwargs)
        try:
            if result._REGISTRY.auto_reduce_dimensions:
                return result.to_reduced_units()
            else:
                return result
        except AttributeError:
            return result

    return wrapped


def ireduce_dimensions(f):
    def wrapped(self, *args, **kwargs):
        result = f(self, *args, **kwargs)
        try:
            if result._REGISTRY.auto_reduce_dimensions:
                result.ito_reduced_units()
        except AttributeError:
            pass
        return result

    return wrapped


def check_implemented(f):
    def wrapped(self, *args, **kwargs):
        other = args[0]
        if is_upcast_type(type(other)):
            return NotImplemented
        # pandas often gets to arrays of quantities [ Q_(1,"m"), Q_(2,"m")]
        # and expects Quantity * array[Quantity] should return NotImplemented
        elif isinstance(other, list) and other and isinstance(other[0], type(self)):
            return NotImplemented
        return f(self, *args, **kwargs)

    return wrapped


def method_wraps(numpy_func):
    if isinstance(numpy_func, str):
        numpy_func = getattr(np, numpy_func, None)

    def wrapper(func):
        func.__wrapped__ = numpy_func

        return func

    return wrapper


def check_dask_array(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        if isinstance(self._magnitude, dask_array.Array):
            return f(self, *args, **kwargs)
        else:
            msg = "Method {} only implemented for objects of {}, not {}".format(
                f.__name__, dask_array.Array, self._magnitude.__class__
            )
            raise AttributeError(msg)

    return wrapper


@contextlib.contextmanager
def printoptions(*args, **kwargs):
    """Numpy printoptions context manager released with version 1.15.0
    https://docs.scipy.org/doc/numpy/reference/generated/numpy.printoptions.html
    """

    opts = np.get_printoptions()
    try:
        np.set_printoptions(*args, **kwargs)
        yield np.get_printoptions()
    finally:
        np.set_printoptions(**opts)


class Quantity(PrettyIPython, SharedRegistryObject):
    """Implements a class to describe a physical quantity:
    the product of a numerical value and a unit of measurement.

    Parameters
    ----------
    value : str, pint.Quantity or any numeric type
        Value of the physical quantity to be created.
    units : UnitsContainer, str or pint.Quantity
        Units of the physical quantity to be created.

    Returns
    -------

    """

    #: Default formatting string.
    default_format = ""

    @property
    def force_ndarray(self):
        return self._REGISTRY.force_ndarray

    @property
    def force_ndarray_like(self):
        return self._REGISTRY.force_ndarray_like

    @property
    def UnitsContainer(self):
        return self._REGISTRY.UnitsContainer

    def __reduce__(self):
        """Allow pickling quantities. Since UnitRegistries are not pickled, upon
        unpickling the new object is always attached to the application registry.
        """
        from . import _unpickle_quantity

        # Note: type(self) would be a mistake as subclasses built by
        # build_quantity_class can't be pickled
        return _unpickle_quantity, (Quantity, self.magnitude, self._units)

    def __new__(cls, value, units=None):
        if is_upcast_type(type(value)):
            raise TypeError(f"Quantity cannot wrap upcast type {type(value)}")
        elif units is None:
            if isinstance(value, str):
                if value == "":
                    raise ValueError(
                        "Expression to parse as Quantity cannot " "be an empty string."
                    )
                ureg = SharedRegistryObject.__new__(cls)._REGISTRY
                inst = ureg.parse_expression(value)
                return cls.__new__(cls, inst)
            elif isinstance(value, cls):
                inst = copy.copy(value)
            else:
                inst = SharedRegistryObject.__new__(cls)
                inst._magnitude = _to_magnitude(
                    value, inst.force_ndarray, inst.force_ndarray_like
                )
                inst._units = inst.UnitsContainer()
        elif isinstance(units, (UnitsContainer, UnitDefinition)):
            inst = SharedRegistryObject.__new__(cls)
            inst._magnitude = _to_magnitude(
                value, inst.force_ndarray, inst.force_ndarray_like
            )
            inst._units = units
        elif isinstance(units, str):
            inst = SharedRegistryObject.__new__(cls)
            inst._magnitude = _to_magnitude(
                value, inst.force_ndarray, inst.force_ndarray_like
            )
            inst._units = inst._REGISTRY.parse_units(units)._units
        elif isinstance(units, SharedRegistryObject):
            if isinstance(units, Quantity) and units.magnitude != 1:
                inst = copy.copy(units)
                logger.warning(
                    "Creating new Quantity using a non unity " "Quantity as units."
                )
            else:
                inst = SharedRegistryObject.__new__(cls)
                inst._units = units._units
            inst._magnitude = _to_magnitude(
                value, inst.force_ndarray, inst.force_ndarray_like
            )
        else:
            raise TypeError(
                "units must be of type str, Quantity or "
                "UnitsContainer; not {}.".format(type(units))
            )

        inst.__used = False
        inst.__handling = None

        return inst

    @property
    def debug_used(self):
        return self.__used

    def __iter__(self):
        # Make sure that, if self.magnitude is not iterable, we raise TypeError as soon
        # as one calls iter(self) without waiting for the first element to be drawn from
        # the iterator
        it_magnitude = iter(self.magnitude)

        def it_outer():
            for element in it_magnitude:
                yield self.__class__(element, self._units)

        return it_outer()

    def __copy__(self):
        ret = self.__class__(copy.copy(self._magnitude), self._units)
        ret.__used = self.__used
        return ret

    def __deepcopy__(self, memo):
        ret = self.__class__(
            copy.deepcopy(self._magnitude, memo), copy.deepcopy(self._units, memo)
        )
        ret.__used = self.__used
        return ret

    def __str__(self):
        if self._REGISTRY.fmt_locale is not None:
            return self.format_babel()

        return format(self)

    def __bytes__(self):
        return str(self).encode(locale.getpreferredencoding())

    def __repr__(self):
        if isinstance(self._magnitude, float):
            return f"<Quantity({self._magnitude:.9}, '{self._units}')>"
        else:
            return f"<Quantity({self._magnitude}, '{self._units}')>"

    def __hash__(self):
        self_base = self.to_base_units()
        if self_base.dimensionless:
            return hash(self_base.magnitude)
        else:
            return hash((self_base.__class__, self_base.magnitude, self_base.units))

    _exp_pattern = re.compile(r"([0-9]\.?[0-9]*)e(-?)\+?0*([0-9]+)")

    def __format__(self, spec):
        if self._REGISTRY.fmt_locale is not None:
            return self.format_babel(spec)

        spec = spec or self.default_format

        # If Compact is selected, do it at the beginning
        if "#" in spec:
            spec = spec.replace("#", "")
            obj = self.to_compact()
        else:
            obj = self

        if "L" in spec:
            allf = plain_allf = r"{}\ {}"
        elif "H" in spec:
            allf = plain_allf = "{} {}"
            if iterable(obj.magnitude):
                # Use HTML table instead of plain text template for array-likes
                allf = (
                    "<table><tbody>"
                    "<tr><th>Magnitude</th>"
                    "<td style='text-align:left;'>{}</td></tr>"
                    "<tr><th>Units</th><td style='text-align:left;'>{}</td></tr>"
                    "</tbody></table>"
                )
        else:
            allf = plain_allf = "{} {}"

        if "Lx" in spec:
            # the LaTeX siunitx code
            spec = spec.replace("Lx", "")
            # TODO: add support for extracting options
            opts = ""
            ustr = siunitx_format_unit(obj.units)
            allf = r"\SI[%s]{{{}}}{{{}}}" % opts
        else:
            # Hand off to unit formatting
            ustr = format(obj.units, spec)

        mspec = remove_custom_flags(spec)
        if "H" in spec:
            # HTML formatting
            if hasattr(obj.magnitude, "_repr_html_"):
                # If magnitude has an HTML repr, nest it within Pint's
                mstr = obj.magnitude._repr_html_()
            else:
                if isinstance(self.magnitude, ndarray):
                    # Use custom ndarray text formatting with monospace font
                    formatter = "{{:{}}}".format(mspec)
                    with printoptions(formatter={"float_kind": formatter.format}):
                        mstr = (
                            "<pre>"
                            + format(obj.magnitude).replace("\n", "<br>")
                            + "</pre>"
                        )
                elif not iterable(obj.magnitude):
                    # Use plain text for scalars
                    mstr = format(obj.magnitude, mspec)
                else:
                    # Use monospace font for other array-likes
                    mstr = (
                        "<pre>"
                        + format(obj.magnitude, mspec).replace("\n", "<br>")
                        + "</pre>"
                    )
        elif isinstance(self.magnitude, ndarray):
            if "L" in spec:
                # Use ndarray LaTeX special formatting
                mstr = ndarray_to_latex(obj.magnitude, mspec)
            else:
                # Use custom ndarray text formatting
                formatter = "{{:{}}}".format(mspec)
                with printoptions(formatter={"float_kind": formatter.format}):
                    mstr = format(obj.magnitude).replace("\n", "")
        else:
            mstr = format(obj.magnitude, mspec).replace("\n", "")

        if "L" in spec:
            mstr = self._exp_pattern.sub(r"\1\\times 10^{\2\3}", mstr)
        elif "H" in spec or "P" in spec:
            m = self._exp_pattern.match(mstr)
            _exp_formatter = (
                _pretty_fmt_exponent if "P" in spec else lambda s: f"<sup>{s}</sup>"
            )
            if m:
                exp = int(m.group(2) + m.group(3))
                mstr = self._exp_pattern.sub(r"\1×10" + _exp_formatter(exp), mstr)

        if allf == plain_allf and ustr.startswith("1 /"):
            # Write e.g. "3 / s" instead of "3 1 / s"
            ustr = ustr[2:]
        return allf.format(mstr, ustr).strip()

    def _repr_pretty_(self, p, cycle):
        if cycle:
            super()._repr_pretty_(p, cycle)
        else:
            p.pretty(self.magnitude)
            p.text(" ")
            p.pretty(self.units)

    def format_babel(self, spec="", **kwspec):
        spec = spec or self.default_format

        # standard cases
        if "#" in spec:
            spec = spec.replace("#", "")
            obj = self.to_compact()
        else:
            obj = self
        kwspec = dict(kwspec)
        if "length" in kwspec:
            kwspec["babel_length"] = kwspec.pop("length")

        loc = kwspec.get("locale", self._REGISTRY.fmt_locale)
        if loc is None:
            raise ValueError("Provide a `locale` value to localize translation.")

        kwspec["locale"] = babel_parse(loc)
        kwspec["babel_plural_form"] = kwspec["locale"].plural_form(obj.magnitude)
        return "{} {}".format(
            format(obj.magnitude, remove_custom_flags(spec)),
            obj.units.format_babel(spec, **kwspec),
        ).replace("\n", "")

    @property
    def magnitude(self):
        """Quantity's magnitude. Long form for `m`"""
        return self._magnitude

    @property
    def m(self):
        """Quantity's magnitude. Short form for `magnitude`"""
        return self._magnitude

    def m_as(self, units):
        """Quantity's magnitude expressed in particular units.

        Parameters
        ----------
        units : pint.Quantity, str or dict
            destination units

        Returns
        -------

        """
        return self.to(units).magnitude

    @property
    def units(self):
        """Quantity's units. Long form for `u`"""
        return self._REGISTRY.Unit(self._units)

    @property
    def u(self):
        """Quantity's units. Short form for `units`"""
        return self._REGISTRY.Unit(self._units)

    @property
    def unitless(self):
        """ """
        return not bool(self.to_root_units()._units)

    @property
    def dimensionless(self):
        """ """
        tmp = self.to_root_units()

        return not bool(tmp.dimensionality)

    _dimensionality = None

    @property
    def dimensionality(self):
        """
        Returns
        -------
        dict
            Dimensionality of the Quantity, e.g. ``{length: 1, time: -1}``
        """
        if self._dimensionality is None:
            self._dimensionality = self._REGISTRY._get_dimensionality(self._units)

        return self._dimensionality

    def check(self, dimension):
        """Return true if the quantity's dimension matches passed dimension.
        """
        return self.dimensionality == self._REGISTRY.get_dimensionality(dimension)

    @classmethod
    def from_list(cls, quant_list, units=None):
        """Transforms a list of Quantities into an numpy.array quantity.
        If no units are specified, the unit of the first element will be used.
        Same as from_sequence.

        If units is not specified and list is empty, the unit cannot be determined
        and a ValueError is raised.

        Parameters
        ----------
        quant_list : list of pint.Quantity
            list of pint.Quantity
        units : UnitsContainer, str or pint.Quantity
            units of the physical quantity to be created (Default value = None)

        Returns
        -------
        pint.Quantity
        """
        return cls.from_sequence(quant_list, units=units)

    @classmethod
    def from_sequence(cls, seq, units=None):
        """Transforms a sequence of Quantities into an numpy.array quantity.
        If no units are specified, the unit of the first element will be used.

        If units is not specified and sequence is empty, the unit cannot be determined
        and a ValueError is raised.

        Parameters
        ----------
        seq : sequence of pint.Quantity
            sequence of pint.Quantity
        units : UnitsContainer, str or pint.Quantity
            units of the physical quantity to be created (Default value = None)

        Returns
        -------
        pint.Quantity
        """

        len_seq = len(seq)
        if units is None:
            if len_seq:
                units = seq[0].u
            else:
                raise ValueError("Cannot determine units from empty sequence!")

        a = np.empty(len_seq)

        for i, seq_i in enumerate(seq):
            a[i] = seq_i.m_as(units)
            # raises DimensionalityError if incompatible units are used in the sequence

        return cls(a, units)

    @classmethod
    def from_tuple(cls, tup):
        return cls(tup[0], cls._REGISTRY.UnitsContainer(tup[1]))

    def to_tuple(self):
        return self.m, tuple(self._units.items())

    def compatible_units(self, *contexts):
        if contexts:
            with self._REGISTRY.context(*contexts):
                return self._REGISTRY.get_compatible_units(self._units)

        return self._REGISTRY.get_compatible_units(self._units)

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
                self.to(other, *contexts, **ctx_kwargs)
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

    def _convert_magnitude_not_inplace(self, other, *contexts, **ctx_kwargs):
        if contexts:
            with self._REGISTRY.context(*contexts, **ctx_kwargs):
                return self._REGISTRY.convert(self._magnitude, self._units, other)

        return self._REGISTRY.convert(self._magnitude, self._units, other)

    def _convert_magnitude(self, other, *contexts, **ctx_kwargs):
        if contexts:
            with self._REGISTRY.context(*contexts, **ctx_kwargs):
                return self._REGISTRY.convert(self._magnitude, self._units, other)

        return self._REGISTRY.convert(
            self._magnitude,
            self._units,
            other,
            inplace=is_duck_array_type(type(self._magnitude)),
        )

    def ito(self, other=None, *contexts, **ctx_kwargs):
        """Inplace rescale to different units.

        Parameters
        ----------
        other : pint.Quantity, str or dict
            Destination units. (Default value = None)
        *contexts : str or pint.Context
            Contexts to use in the transformation.
        **ctx_kwargs :
            Values for the Context/s
        """
        other = to_units_container(other, self._REGISTRY)

        self._magnitude = self._convert_magnitude(other, *contexts, **ctx_kwargs)
        self._units = other

        return None

    def to(self, other=None, *contexts, **ctx_kwargs):
        """Return Quantity rescaled to different units.

        Parameters
        ----------
        other : pint.Quantity, str or dict
            destination units. (Default value = None)
        *contexts : str or pint.Context
            Contexts to use in the transformation.
        **ctx_kwargs :
            Values for the Context/s

        Returns
        -------
        pint.Quantity
        """
        other = to_units_container(other, self._REGISTRY)

        magnitude = self._convert_magnitude_not_inplace(other, *contexts, **ctx_kwargs)

        return self.__class__(magnitude, other)

    def ito_root_units(self):
        """Return Quantity rescaled to root units."""

        _, other = self._REGISTRY._get_root_units(self._units)

        self._magnitude = self._convert_magnitude(other)
        self._units = other

        return None

    def to_root_units(self):
        """Return Quantity rescaled to root units."""

        _, other = self._REGISTRY._get_root_units(self._units)

        magnitude = self._convert_magnitude_not_inplace(other)

        return self.__class__(magnitude, other)

    def ito_base_units(self):
        """Return Quantity rescaled to base units."""

        _, other = self._REGISTRY._get_base_units(self._units)

        self._magnitude = self._convert_magnitude(other)
        self._units = other

        return None

    def to_base_units(self):
        """Return Quantity rescaled to base units."""

        _, other = self._REGISTRY._get_base_units(self._units)

        magnitude = self._convert_magnitude_not_inplace(other)

        return self.__class__(magnitude, other)

    def ito_reduced_units(self):
        """Return Quantity scaled in place to reduced units, i.e. one unit per
        dimension. This will not reduce compound units (e.g., 'J/kg' will not
        be reduced to m**2/s**2), nor can it make use of contexts at this time.
        """

        # shortcuts in case we're dimensionless or only a single unit
        if self.dimensionless:
            return self.ito({})
        if len(self._units) == 1:
            return None

        newunits = self._units.copy()
        # loop through individual units and compare to each other unit
        # can we do better than a nested loop here?
        for unit1, exp in self._units.items():
            # make sure it wasn't already reduced to zero exponent on prior pass
            if unit1 not in newunits:
                continue
            for unit2 in newunits:
                if unit1 != unit2:
                    power = self._REGISTRY._get_dimensionality_ratio(unit1, unit2)
                    if power:
                        newunits = newunits.add(unit2, exp / power).remove([unit1])
                        break

        return self.ito(newunits)

    def to_reduced_units(self):
        """Return Quantity scaled in place to reduced units, i.e. one unit per
        dimension. This will not reduce compound units (intentionally), nor
        can it make use of contexts at this time.
        """

        # can we make this more efficient?
        newq = copy.copy(self)
        newq.ito_reduced_units()
        return newq

    def to_compact(self, unit=None):
        """"Return Quantity rescaled to compact, human-readable units.

        To get output in terms of a different unit, use the unit parameter.


        Example
        -------

        >>> import pint
        >>> ureg = pint.UnitRegistry()
        >>> (200e-9*ureg.s).to_compact()
        <Quantity(200.0, 'nanosecond')>
        >>> (1e-2*ureg('kg m/s^2')).to_compact('N')
        <Quantity(10.0, 'millinewton')>
        """

        if not isinstance(self.magnitude, numbers.Number):
            msg = (
                "to_compact applied to non numerical types "
                "has an undefined behavior."
            )
            w = RuntimeWarning(msg)
            warnings.warn(w, stacklevel=2)
            return self

        if (
            self.unitless
            or self.magnitude == 0
            or math.isnan(self.magnitude)
            or math.isinf(self.magnitude)
        ):
            return self

        SI_prefixes = {}
        for prefix in self._REGISTRY._prefixes.values():
            try:
                scale = prefix.converter.scale
                # Kludgy way to check if this is an SI prefix
                log10_scale = int(math.log10(scale))
                if log10_scale == math.log10(scale):
                    SI_prefixes[log10_scale] = prefix.name
            except Exception:
                SI_prefixes[0] = ""

        SI_prefixes = sorted(SI_prefixes.items())
        SI_powers = [item[0] for item in SI_prefixes]
        SI_bases = [item[1] for item in SI_prefixes]

        if unit is None:
            unit = infer_base_unit(self)
        else:
            unit = infer_base_unit(self.__class__(1, unit))

        q_base = self.to(unit)

        magnitude = q_base.magnitude

        units = list(q_base._units.items())
        units_numerator = [a for a in units if a[1] > 0]

        if len(units_numerator) > 0:
            unit_str, unit_power = units_numerator[0]
        else:
            unit_str, unit_power = units[0]

        if unit_power > 0:
            power = int(math.floor(math.log10(abs(magnitude)) / unit_power / 3)) * 3
        else:
            power = int(math.ceil(math.log10(abs(magnitude)) / unit_power / 3)) * 3

        index = bisect.bisect_left(SI_powers, power)

        if index >= len(SI_bases):
            index = -1

        prefix = SI_bases[index]

        new_unit_str = prefix + unit_str
        new_unit_container = q_base._units.rename(unit_str, new_unit_str)

        return self.to(new_unit_container)

    # Mathematical operations
    def __int__(self):
        if self.dimensionless:
            return int(self._convert_magnitude_not_inplace(UnitsContainer()))
        raise DimensionalityError(self._units, "dimensionless")

    def __float__(self):
        if self.dimensionless:
            return float(self._convert_magnitude_not_inplace(UnitsContainer()))
        raise DimensionalityError(self._units, "dimensionless")

    def __complex__(self):
        if self.dimensionless:
            return complex(self._convert_magnitude_not_inplace(UnitsContainer()))
        raise DimensionalityError(self._units, "dimensionless")

    @check_implemented
    def _iadd_sub(self, other, op):
        """Perform addition or subtraction operation in-place and return the result.

        Parameters
        ----------
        other : pint.Quantity or any type accepted by :func:`_to_magnitude`
            object to be added to / subtracted from self
        op : function
            operator function (e.g. operator.add, operator.isub)

        """
        if not self._check(other):
            # other not from same Registry or not a Quantity
            try:
                other_magnitude = _to_magnitude(
                    other, self.force_ndarray, self.force_ndarray_like
                )
            except PintTypeError:
                raise
            except TypeError:
                return NotImplemented
            if zero_or_nan(other, True):
                # If the other value is 0 (but not Quantity 0)
                # do the operation without checking units.
                # We do the calculation instead of just returning the same
                # value to enforce any shape checking and type casting due to
                # the operation.
                self._magnitude = op(self._magnitude, other_magnitude)
            elif self.dimensionless:
                self.ito(self.UnitsContainer())
                self._magnitude = op(self._magnitude, other_magnitude)
            else:
                raise DimensionalityError(self._units, "dimensionless")
            return self

        if not self.dimensionality == other.dimensionality:
            raise DimensionalityError(
                self._units, other._units, self.dimensionality, other.dimensionality
            )

        # Next we define some variables to make if-clauses more readable.
        self_non_mul_units = self._get_non_multiplicative_units()
        is_self_multiplicative = len(self_non_mul_units) == 0
        if len(self_non_mul_units) == 1:
            self_non_mul_unit = self_non_mul_units[0]
        other_non_mul_units = other._get_non_multiplicative_units()
        is_other_multiplicative = len(other_non_mul_units) == 0
        if len(other_non_mul_units) == 1:
            other_non_mul_unit = other_non_mul_units[0]

        # Presence of non-multiplicative units gives rise to several cases.
        if is_self_multiplicative and is_other_multiplicative:
            if self._units == other._units:
                self._magnitude = op(self._magnitude, other._magnitude)
            # If only self has a delta unit, other determines unit of result.
            elif self._get_delta_units() and not other._get_delta_units():
                self._magnitude = op(
                    self._convert_magnitude(other._units), other._magnitude
                )
                self._units = other._units
            else:
                self._magnitude = op(self._magnitude, other.to(self._units)._magnitude)

        elif (
            op == operator.isub
            and len(self_non_mul_units) == 1
            and self._units[self_non_mul_unit] == 1
            and not other._has_compatible_delta(self_non_mul_unit)
        ):
            if self._units == other._units:
                self._magnitude = op(self._magnitude, other._magnitude)
            else:
                self._magnitude = op(self._magnitude, other.to(self._units)._magnitude)
            self._units = self._units.rename(
                self_non_mul_unit, "delta_" + self_non_mul_unit
            )

        elif (
            op == operator.isub
            and len(other_non_mul_units) == 1
            and other._units[other_non_mul_unit] == 1
            and not self._has_compatible_delta(other_non_mul_unit)
        ):
            # we convert to self directly since it is multiplicative
            self._magnitude = op(self._magnitude, other.to(self._units)._magnitude)

        elif (
            len(self_non_mul_units) == 1
            # order of the dimension of offset unit == 1 ?
            and self._units[self_non_mul_unit] == 1
            and other._has_compatible_delta(self_non_mul_unit)
        ):
            # Replace offset unit in self by the corresponding delta unit.
            # This is done to prevent a shift by offset in the to()-call.
            tu = self._units.rename(self_non_mul_unit, "delta_" + self_non_mul_unit)
            self._magnitude = op(self._magnitude, other.to(tu)._magnitude)
        elif (
            len(other_non_mul_units) == 1
            # order of the dimension of offset unit == 1 ?
            and other._units[other_non_mul_unit] == 1
            and self._has_compatible_delta(other_non_mul_unit)
        ):
            # Replace offset unit in other by the corresponding delta unit.
            # This is done to prevent a shift by offset in the to()-call.
            tu = other._units.rename(other_non_mul_unit, "delta_" + other_non_mul_unit)
            self._magnitude = op(self._convert_magnitude(tu), other._magnitude)
            self._units = other._units
        else:
            raise OffsetUnitCalculusError(self._units, other._units)

        return self

    @check_implemented
    def _add_sub(self, other, op):
        """Perform addition or subtraction operation and return the result.

        Parameters
        ----------
        other : pint.Quantity or any type accepted by :func:`_to_magnitude`
            object to be added to / subtracted from self
        op : function
            operator function (e.g. operator.add, operator.isub)
        """
        if not self._check(other):
            # other not from same Registry or not a Quantity
            if zero_or_nan(other, True):
                # If the other value is 0 or NaN (but not a Quantity)
                # do the operation without checking units.
                # We do the calculation instead of just returning the same
                # value to enforce any shape checking and type casting due to
                # the operation.
                units = self._units
                magnitude = op(
                    self._magnitude,
                    _to_magnitude(other, self.force_ndarray, self.force_ndarray_like),
                )
            elif self.dimensionless:
                units = self.UnitsContainer()
                magnitude = op(
                    self.to(units)._magnitude,
                    _to_magnitude(other, self.force_ndarray, self.force_ndarray_like),
                )
            else:
                raise DimensionalityError(self._units, "dimensionless")
            return self.__class__(magnitude, units)

        if not self.dimensionality == other.dimensionality:
            raise DimensionalityError(
                self._units, other._units, self.dimensionality, other.dimensionality
            )

        # Next we define some variables to make if-clauses more readable.
        self_non_mul_units = self._get_non_multiplicative_units()
        is_self_multiplicative = len(self_non_mul_units) == 0
        if len(self_non_mul_units) == 1:
            self_non_mul_unit = self_non_mul_units[0]
        other_non_mul_units = other._get_non_multiplicative_units()
        is_other_multiplicative = len(other_non_mul_units) == 0
        if len(other_non_mul_units) == 1:
            other_non_mul_unit = other_non_mul_units[0]

        # Presence of non-multiplicative units gives rise to several cases.
        if is_self_multiplicative and is_other_multiplicative:
            if self._units == other._units:
                magnitude = op(self._magnitude, other._magnitude)
                units = self._units
            # If only self has a delta unit, other determines unit of result.
            elif self._get_delta_units() and not other._get_delta_units():
                magnitude = op(
                    self._convert_magnitude_not_inplace(other._units), other._magnitude
                )
                units = other._units
            else:
                units = self._units
                magnitude = op(self._magnitude, other.to(self._units).magnitude)

        elif (
            op == operator.sub
            and len(self_non_mul_units) == 1
            and self._units[self_non_mul_unit] == 1
            and not other._has_compatible_delta(self_non_mul_unit)
        ):
            if self._units == other._units:
                magnitude = op(self._magnitude, other._magnitude)
            else:
                magnitude = op(self._magnitude, other.to(self._units)._magnitude)
            units = self._units.rename(self_non_mul_unit, "delta_" + self_non_mul_unit)

        elif (
            op == operator.sub
            and len(other_non_mul_units) == 1
            and other._units[other_non_mul_unit] == 1
            and not self._has_compatible_delta(other_non_mul_unit)
        ):
            # we convert to self directly since it is multiplicative
            magnitude = op(self._magnitude, other.to(self._units)._magnitude)
            units = self._units

        elif (
            len(self_non_mul_units) == 1
            # order of the dimension of offset unit == 1 ?
            and self._units[self_non_mul_unit] == 1
            and other._has_compatible_delta(self_non_mul_unit)
        ):
            # Replace offset unit in self by the corresponding delta unit.
            # This is done to prevent a shift by offset in the to()-call.
            tu = self._units.rename(self_non_mul_unit, "delta_" + self_non_mul_unit)
            magnitude = op(self._magnitude, other.to(tu).magnitude)
            units = self._units
        elif (
            len(other_non_mul_units) == 1
            # order of the dimension of offset unit == 1 ?
            and other._units[other_non_mul_unit] == 1
            and self._has_compatible_delta(other_non_mul_unit)
        ):
            # Replace offset unit in other by the corresponding delta unit.
            # This is done to prevent a shift by offset in the to()-call.
            tu = other._units.rename(other_non_mul_unit, "delta_" + other_non_mul_unit)
            magnitude = op(self._convert_magnitude_not_inplace(tu), other._magnitude)
            units = other._units
        else:
            raise OffsetUnitCalculusError(self._units, other._units)

        return self.__class__(magnitude, units)

    def __iadd__(self, other):
        if isinstance(other, datetime.datetime):
            return self.to_timedelta() + other
        elif is_duck_array_type(type(self._magnitude)):
            return self._iadd_sub(other, operator.iadd)
        else:
            return self._add_sub(other, operator.add)

    def __add__(self, other):
        if isinstance(other, datetime.datetime):
            return self.to_timedelta() + other
        else:
            return self._add_sub(other, operator.add)

    __radd__ = __add__

    def __isub__(self, other):
        if is_duck_array_type(type(self._magnitude)):
            return self._iadd_sub(other, operator.isub)
        else:
            return self._add_sub(other, operator.sub)

    def __sub__(self, other):
        return self._add_sub(other, operator.sub)

    def __rsub__(self, other):
        if isinstance(other, datetime.datetime):
            return other - self.to_timedelta()
        else:
            return -self._add_sub(other, operator.sub)

    @check_implemented
    @ireduce_dimensions
    def _imul_div(self, other, magnitude_op, units_op=None):
        """Perform multiplication or division operation in-place and return the
        result.

        Parameters
        ----------
        other : pint.Quantity or any type accepted by :func:`_to_magnitude`
            object to be multiplied/divided with self
        magnitude_op : function
            operator function to perform on the magnitudes
            (e.g. operator.mul)
        units_op : function or None
            operator function to perform on the units; if None,
            *magnitude_op* is used (Default value = None)

        Returns
        -------

        """
        if units_op is None:
            units_op = magnitude_op

        offset_units_self = self._get_non_multiplicative_units()
        no_offset_units_self = len(offset_units_self)

        if not self._check(other):

            if not self._ok_for_muldiv(no_offset_units_self):
                raise OffsetUnitCalculusError(self._units, getattr(other, "units", ""))
            if len(offset_units_self) == 1:
                if self._units[offset_units_self[0]] != 1 or magnitude_op not in [
                    operator.mul,
                    operator.imul,
                ]:
                    raise OffsetUnitCalculusError(
                        self._units, getattr(other, "units", "")
                    )
            try:
                other_magnitude = _to_magnitude(
                    other, self.force_ndarray, self.force_ndarray_like
                )
            except PintTypeError:
                raise
            except TypeError:
                return NotImplemented
            self._magnitude = magnitude_op(self._magnitude, other_magnitude)
            self._units = units_op(self._units, self.UnitsContainer())
            return self

        if isinstance(other, self._REGISTRY.Unit):
            other = 1 * other

        if not self._ok_for_muldiv(no_offset_units_self):
            raise OffsetUnitCalculusError(self._units, other._units)
        elif no_offset_units_self == 1 and len(self._units) == 1:
            self.ito_root_units()

        no_offset_units_other = len(other._get_non_multiplicative_units())

        if not other._ok_for_muldiv(no_offset_units_other):
            raise OffsetUnitCalculusError(self._units, other._units)
        elif no_offset_units_other == 1 and len(other._units) == 1:
            other.ito_root_units()

        self._magnitude = magnitude_op(self._magnitude, other._magnitude)
        self._units = units_op(self._units, other._units)

        return self

    @check_implemented
    @ireduce_dimensions
    def _mul_div(self, other, magnitude_op, units_op=None):
        """Perform multiplication or division operation and return the result.

        Parameters
        ----------
        other : pint.Quantity or any type accepted by :func:`_to_magnitude`
            object to be multiplied/divided with self
        magnitude_op : function
            operator function to perform on the magnitudes
            (e.g. operator.mul)
        units_op : function or None
            operator function to perform on the units; if None,
            *magnitude_op* is used (Default value = None)

        Returns
        -------

        """
        if units_op is None:
            units_op = magnitude_op

        offset_units_self = self._get_non_multiplicative_units()
        no_offset_units_self = len(offset_units_self)

        if not self._check(other):

            if not self._ok_for_muldiv(no_offset_units_self):
                raise OffsetUnitCalculusError(self._units, getattr(other, "units", ""))
            if len(offset_units_self) == 1:
                if self._units[offset_units_self[0]] != 1 or magnitude_op not in [
                    operator.mul,
                    operator.imul,
                ]:
                    raise OffsetUnitCalculusError(
                        self._units, getattr(other, "units", "")
                    )
            try:
                other_magnitude = _to_magnitude(
                    other, self.force_ndarray, self.force_ndarray_like
                )
            except PintTypeError:
                raise
            except TypeError:
                return NotImplemented

            magnitude = magnitude_op(self._magnitude, other_magnitude)
            units = units_op(self._units, self.UnitsContainer())

            return self.__class__(magnitude, units)

        if isinstance(other, self._REGISTRY.Unit):
            other = 1 * other

        new_self = self

        if not self._ok_for_muldiv(no_offset_units_self):
            raise OffsetUnitCalculusError(self._units, other._units)
        elif no_offset_units_self == 1 and len(self._units) == 1:
            new_self = self.to_root_units()

        no_offset_units_other = len(other._get_non_multiplicative_units())

        if not other._ok_for_muldiv(no_offset_units_other):
            raise OffsetUnitCalculusError(self._units, other._units)
        elif no_offset_units_other == 1 and len(other._units) == 1:
            other = other.to_root_units()

        magnitude = magnitude_op(new_self._magnitude, other._magnitude)
        units = units_op(new_self._units, other._units)

        return self.__class__(magnitude, units)

    def __imul__(self, other):
        if is_duck_array_type(type(self._magnitude)):
            return self._imul_div(other, operator.imul)
        else:
            return self._mul_div(other, operator.mul)

    def __mul__(self, other):
        return self._mul_div(other, operator.mul)

    __rmul__ = __mul__

    def __matmul__(self, other):
        # Use NumPy ufunc (existing since 1.16) for matrix multiplication
        if version.parse(NUMPY_VER) >= version.parse("1.16"):
            return np.matmul(self, other)
        else:
            return NotImplemented

    __rmatmul__ = __matmul__

    def __itruediv__(self, other):
        if is_duck_array_type(type(self._magnitude)):
            return self._imul_div(other, operator.itruediv)
        else:
            return self._mul_div(other, operator.truediv)

    def __truediv__(self, other):
        return self._mul_div(other, operator.truediv)

    def __rtruediv__(self, other):
        try:
            other_magnitude = _to_magnitude(
                other, self.force_ndarray, self.force_ndarray_like
            )
        except PintTypeError:
            raise
        except TypeError:
            return NotImplemented

        no_offset_units_self = len(self._get_non_multiplicative_units())
        if not self._ok_for_muldiv(no_offset_units_self):
            raise OffsetUnitCalculusError(self._units, "")
        elif no_offset_units_self == 1 and len(self._units) == 1:
            self = self.to_root_units()

        return self.__class__(other_magnitude / self._magnitude, 1 / self._units)

    __div__ = __truediv__
    __rdiv__ = __rtruediv__
    __idiv__ = __itruediv__

    def __ifloordiv__(self, other):
        if self._check(other):
            self._magnitude //= other.to(self._units)._magnitude
        elif self.dimensionless:
            self._magnitude = self.to("")._magnitude // other
        else:
            raise DimensionalityError(self._units, "dimensionless")
        self._units = self.UnitsContainer({})
        return self

    @check_implemented
    def __floordiv__(self, other):
        if self._check(other):
            magnitude = self._magnitude // other.to(self._units)._magnitude
        elif self.dimensionless:
            magnitude = self.to("")._magnitude // other
        else:
            raise DimensionalityError(self._units, "dimensionless")
        return self.__class__(magnitude, self.UnitsContainer({}))

    @check_implemented
    def __rfloordiv__(self, other):
        if self._check(other):
            magnitude = other._magnitude // self.to(other._units)._magnitude
        elif self.dimensionless:
            magnitude = other // self.to("")._magnitude
        else:
            raise DimensionalityError(self._units, "dimensionless")
        return self.__class__(magnitude, self.UnitsContainer({}))

    @check_implemented
    def __imod__(self, other):
        if not self._check(other):
            other = self.__class__(other, self.UnitsContainer({}))
        self._magnitude %= other.to(self._units)._magnitude
        return self

    @check_implemented
    def __mod__(self, other):
        if not self._check(other):
            other = self.__class__(other, self.UnitsContainer({}))
        magnitude = self._magnitude % other.to(self._units)._magnitude
        return self.__class__(magnitude, self._units)

    @check_implemented
    def __rmod__(self, other):
        if self._check(other):
            magnitude = other._magnitude % self.to(other._units)._magnitude
            return self.__class__(magnitude, other._units)
        elif self.dimensionless:
            magnitude = other % self.to("")._magnitude
            return self.__class__(magnitude, self.UnitsContainer({}))
        else:
            raise DimensionalityError(self._units, "dimensionless")

    @check_implemented
    def __divmod__(self, other):
        if not self._check(other):
            other = self.__class__(other, self.UnitsContainer({}))
        q, r = divmod(self._magnitude, other.to(self._units)._magnitude)
        return (
            self.__class__(q, self.UnitsContainer({})),
            self.__class__(r, self._units),
        )

    @check_implemented
    def __rdivmod__(self, other):
        if self._check(other):
            q, r = divmod(other._magnitude, self.to(other._units)._magnitude)
            unit = other._units
        elif self.dimensionless:
            q, r = divmod(other, self.to("")._magnitude)
            unit = self.UnitsContainer({})
        else:
            raise DimensionalityError(self._units, "dimensionless")
        return (self.__class__(q, self.UnitsContainer({})), self.__class__(r, unit))

    @check_implemented
    def __ipow__(self, other):
        if not is_duck_array_type(type(self._magnitude)):
            return self.__pow__(other)

        try:
            _to_magnitude(other, self.force_ndarray, self.force_ndarray_like)
        except PintTypeError:
            raise
        except TypeError:
            return NotImplemented
        else:
            if not self._ok_for_muldiv:
                raise OffsetUnitCalculusError(self._units)

            if is_duck_array_type(type(getattr(other, "_magnitude", other))):
                # arrays are refused as exponent, because they would create
                # len(array) quantities of len(set(array)) different units
                # unless the base is dimensionless.
                if self.dimensionless:
                    if getattr(other, "dimensionless", False):
                        self._magnitude **= other.m_as("")
                        return self
                    elif not getattr(other, "dimensionless", True):
                        raise DimensionalityError(other._units, "dimensionless")
                    else:
                        self._magnitude **= other
                        return self
                elif np.size(other) > 1:
                    raise DimensionalityError(
                        self._units,
                        "dimensionless",
                        extra_msg=". Quantity array exponents are only allowed if the "
                        "base is dimensionless",
                    )

            if other == 1:
                return self
            elif other == 0:
                self._units = self.UnitsContainer()
            else:
                if not self._is_multiplicative:
                    if self._REGISTRY.autoconvert_offset_to_baseunit:
                        self.ito_base_units()
                    else:
                        raise OffsetUnitCalculusError(self._units)

                if getattr(other, "dimensionless", False):
                    other = other.to_base_units().magnitude
                    self._units **= other
                elif not getattr(other, "dimensionless", True):
                    raise DimensionalityError(self._units, "dimensionless")
                else:
                    self._units **= other

            self._magnitude **= _to_magnitude(
                other, self.force_ndarray, self.force_ndarray_like
            )
            return self

    @check_implemented
    def __pow__(self, other):
        try:
            _to_magnitude(other, self.force_ndarray, self.force_ndarray_like)
        except PintTypeError:
            raise
        except TypeError:
            return NotImplemented
        else:
            if not self._ok_for_muldiv:
                raise OffsetUnitCalculusError(self._units)

            if is_duck_array_type(type(getattr(other, "_magnitude", other))):
                # arrays are refused as exponent, because they would create
                # len(array) quantities of len(set(array)) different units
                # unless the base is dimensionless.
                if self.dimensionless:
                    if getattr(other, "dimensionless", False):
                        return self.__class__(self.m ** other.m_as(""))
                    elif not getattr(other, "dimensionless", True):
                        raise DimensionalityError(other._units, "dimensionless")
                    else:
                        return self.__class__(self.m ** other)
                elif np.size(other) > 1:
                    raise DimensionalityError(
                        self._units,
                        "dimensionless",
                        extra_msg=". Quantity array exponents are only allowed if the "
                        "base is dimensionless",
                    )

            new_self = self
            if other == 1:
                return self
            elif other == 0:
                exponent = 0
                units = self.UnitsContainer()
            else:
                if not self._is_multiplicative:
                    if self._REGISTRY.autoconvert_offset_to_baseunit:
                        new_self = self.to_root_units()
                    else:
                        raise OffsetUnitCalculusError(self._units)

                if getattr(other, "dimensionless", False):
                    exponent = other.to_root_units().magnitude
                    units = new_self._units ** exponent
                elif not getattr(other, "dimensionless", True):
                    raise DimensionalityError(other._units, "dimensionless")
                else:
                    exponent = _to_magnitude(
                        other, self.force_ndarray, self.force_ndarray_like
                    )
                    units = new_self._units ** exponent

            magnitude = new_self._magnitude ** exponent
            return self.__class__(magnitude, units)

    @check_implemented
    def __rpow__(self, other):
        try:
            _to_magnitude(other, self.force_ndarray, self.force_ndarray_like)
        except PintTypeError:
            raise
        except TypeError:
            return NotImplemented
        else:
            if not self.dimensionless:
                raise DimensionalityError(self._units, "dimensionless")
            new_self = self.to_root_units()
            return other ** new_self._magnitude

    def __abs__(self):
        return self.__class__(abs(self._magnitude), self._units)

    def __round__(self, ndigits=0):
        return self.__class__(round(self._magnitude, ndigits=ndigits), self._units)

    def __pos__(self):
        return self.__class__(operator.pos(self._magnitude), self._units)

    def __neg__(self):
        return self.__class__(operator.neg(self._magnitude), self._units)

    @check_implemented
    def __eq__(self, other):
        def bool_result(value):
            nonlocal other

            if not is_duck_array_type(type(self._magnitude)):
                return value

            if isinstance(other, Quantity):
                other = other._magnitude

            template, _ = np.broadcast_arrays(self._magnitude, other)
            return np.full_like(template, fill_value=value, dtype=np.bool_)

        # We compare to the base class of Quantity because
        # each Quantity class is unique.
        if not isinstance(other, Quantity):
            if zero_or_nan(other, True):
                # Handle the special case in which we compare to zero or NaN
                # (or an array of zeros or NaNs)
                if self._is_multiplicative:
                    # compare magnitude
                    return eq(self._magnitude, other, False)
                else:
                    # compare the magnitude after converting the
                    # non-multiplicative quantity to base units
                    if self._REGISTRY.autoconvert_offset_to_baseunit:
                        return eq(self.to_base_units()._magnitude, other, False)
                    else:
                        raise OffsetUnitCalculusError(self._units)

            if self.dimensionless:
                return eq(
                    self._convert_magnitude_not_inplace(self.UnitsContainer()),
                    other,
                    False,
                )

            return bool_result(False)

        # TODO: this might be expensive. Do we even need it?
        if eq(self._magnitude, 0, True) and eq(other._magnitude, 0, True):
            return bool_result(self.dimensionality == other.dimensionality)

        if self._units == other._units:
            return eq(self._magnitude, other._magnitude, False)

        try:
            return eq(
                self._convert_magnitude_not_inplace(other._units),
                other._magnitude,
                False,
            )
        except DimensionalityError:
            return bool_result(False)

    @check_implemented
    def __ne__(self, other):
        out = self.__eq__(other)
        if is_duck_array_type(type(out)):
            return np.logical_not(out)
        return not out

    @check_implemented
    def compare(self, other, op):
        if not isinstance(other, self.__class__):
            if self.dimensionless:
                return op(
                    self._convert_magnitude_not_inplace(self.UnitsContainer()), other
                )
            elif zero_or_nan(other, True):
                # Handle the special case in which we compare to zero or NaN
                # (or an array of zeros or NaNs)
                if self._is_multiplicative:
                    # compare magnitude
                    return op(self._magnitude, other)
                else:
                    # compare the magnitude after converting the
                    # non-multiplicative quantity to base units
                    if self._REGISTRY.autoconvert_offset_to_baseunit:
                        return op(self.to_base_units()._magnitude, other)
                    else:
                        raise OffsetUnitCalculusError(self._units)
            else:
                raise ValueError("Cannot compare Quantity and {}".format(type(other)))

        if self._units == other._units:
            return op(self._magnitude, other._magnitude)
        if self.dimensionality != other.dimensionality:
            raise DimensionalityError(
                self._units, other._units, self.dimensionality, other.dimensionality
            )
        return op(self.to_root_units().magnitude, other.to_root_units().magnitude)

    __lt__ = lambda self, other: self.compare(other, op=operator.lt)
    __le__ = lambda self, other: self.compare(other, op=operator.le)
    __ge__ = lambda self, other: self.compare(other, op=operator.ge)
    __gt__ = lambda self, other: self.compare(other, op=operator.gt)

    def __bool__(self):
        # Only cast when non-ambiguous (when multiplicative unit)
        if self._is_multiplicative:
            return bool(self._magnitude)
        else:
            raise ValueError("Boolean value of Quantity with offset unit is ambiguous.")

    __nonzero__ = __bool__

    # NumPy function/ufunc support
    __array_priority__ = 17

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        if method != "__call__":
            # Only handle ufuncs as callables
            return NotImplemented

        # Replicate types from __array_function__
        types = set(
            type(arg)
            for arg in list(inputs) + list(kwargs.values())
            if hasattr(arg, "__array_ufunc__")
        )

        return numpy_wrap("ufunc", ufunc, inputs, kwargs, types)

    def __array_function__(self, func, types, args, kwargs):
        return numpy_wrap("function", func, args, kwargs, types)

    _wrapped_numpy_methods = ["flatten", "astype", "item"]

    def _numpy_method_wrap(self, func, *args, **kwargs):
        """Convenience method to wrap on the fly NumPy ndarray methods taking
        care of the units.
        """

        # Set input units if needed
        if func.__name__ in set_units_ufuncs:
            self.__ito_if_needed(set_units_ufuncs[func.__name__][0])

        value = func(*args, **kwargs)

        # Set output units as needed
        if func.__name__ in (
            matching_input_copy_units_output_ufuncs
            + copy_units_output_ufuncs
            + self._wrapped_numpy_methods
        ):
            output_unit = self._units
        elif func.__name__ in set_units_ufuncs:
            output_unit = set_units_ufuncs[func.__name__][1]
        elif func.__name__ in matching_input_set_units_output_ufuncs:
            output_unit = matching_input_set_units_output_ufuncs[func.__name__]
        elif func.__name__ in op_units_output_ufuncs:
            output_unit = get_op_output_unit(
                op_units_output_ufuncs[func.__name__],
                self.units,
                list(args) + list(kwargs.values()),
                self._magnitude.size,
            )
        else:
            output_unit = None

        if output_unit is not None:
            return self.__class__(value, output_unit)
        else:
            return value

    def __array__(self, t=None):
        warnings.warn(
            "The unit of the quantity is stripped when downcasting to ndarray.",
            UnitStrippedWarning,
            stacklevel=2,
        )
        return _to_magnitude(self._magnitude, force_ndarray=True)

    def clip(self, first=None, second=None, out=None, **kwargs):
        minimum = kwargs.get("min", first)
        maximum = kwargs.get("max", second)

        if minimum is None and maximum is None:
            raise TypeError("clip() takes at least 3 arguments (2 given)")

        if maximum is None and "min" not in kwargs:
            minimum, maximum = maximum, minimum

        kwargs = {"out": out}

        if minimum is not None:
            if isinstance(minimum, self.__class__):
                kwargs["min"] = minimum.to(self).magnitude
            elif self.dimensionless:
                kwargs["min"] = minimum
            else:
                raise DimensionalityError("dimensionless", self._units)

        if maximum is not None:
            if isinstance(maximum, self.__class__):
                kwargs["max"] = maximum.to(self).magnitude
            elif self.dimensionless:
                kwargs["max"] = maximum
            else:
                raise DimensionalityError("dimensionless", self._units)

        return self.__class__(self.magnitude.clip(**kwargs), self._units)

    def fill(self, value):
        self._units = value._units
        return self.magnitude.fill(value.magnitude)

    def put(self, indices, values, mode="raise"):
        if isinstance(values, self.__class__):
            values = values.to(self).magnitude
        elif self.dimensionless:
            values = self.__class__(values, "").to(self)
        else:
            raise DimensionalityError("dimensionless", self._units)
        self.magnitude.put(indices, values, mode)

    @property
    def real(self):
        return self.__class__(self._magnitude.real, self._units)

    @property
    def imag(self):
        return self.__class__(self._magnitude.imag, self._units)

    @property
    def T(self):
        return self.__class__(self._magnitude.T, self._units)

    @property
    def flat(self):
        for v in self._magnitude.flat:
            yield self.__class__(v, self._units)

    @property
    def shape(self):
        return self._magnitude.shape

    @shape.setter
    def shape(self, value):
        self._magnitude.shape = value

    def searchsorted(self, v, side="left", sorter=None):
        if isinstance(v, self.__class__):
            v = v.to(self).magnitude
        elif self.dimensionless:
            v = self.__class__(v, "").to(self)
        else:
            raise DimensionalityError("dimensionless", self._units)
        return self.magnitude.searchsorted(v, side)

    def dot(self, b):
        """Dot product of two arrays.

        Wraps np.dot().
        """

        return np.dot(self, b)

    @method_wraps("prod")
    def prod(self, *args, **kwargs):
        """ Return the product of quantity elements over a given axis

        Wraps np.prod().
        """
        # TODO: remove after support for 1.16 has been dropped
        if not HAS_NUMPY_ARRAY_FUNCTION:
            raise NotImplementedError(
                "prod is only defined for"
                " numpy == 1.16 with NUMPY_ARRAY_FUNCTION_PROTOCOL enabled"
                f" or for numpy >= 1.17 ({np.__version__} is installed)."
                " Please try setting the NUMPY_ARRAY_FUNCTION_PROTOCOL environment variable"
                " or updating your numpy version."
            )
        return np.prod(self, *args, **kwargs)

    def __ito_if_needed(self, to_units):
        if self.unitless and to_units == "radian":
            return

        self.ito(to_units)

    def __len__(self):
        return len(self._magnitude)

    def __getattr__(self, item):
        if item.startswith("__array_"):
            # Handle array protocol attributes other than `__array__`
            raise AttributeError(f"Array protocol attribute {item} not available.")
        elif item in HANDLED_UFUNCS or item in self._wrapped_numpy_methods:
            magnitude_as_duck_array = _to_magnitude(
                self._magnitude, force_ndarray_like=True
            )
            try:
                attr = getattr(magnitude_as_duck_array, item)
                return functools.partial(self._numpy_method_wrap, attr)
            except AttributeError:
                raise AttributeError(
                    f"NumPy method {item} not available on {type(magnitude_as_duck_array)}"
                )
            except TypeError as exc:
                if "not callable" in str(exc):
                    raise AttributeError(
                        f"NumPy method {item} not callable on {type(magnitude_as_duck_array)}"
                    )
                else:
                    raise exc

        try:
            return getattr(self._magnitude, item)
        except AttributeError:
            raise AttributeError(
                "Neither Quantity object nor its magnitude ({}) "
                "has attribute '{}'".format(self._magnitude, item)
            )

    def __getitem__(self, key):
        try:
            return type(self)(self._magnitude[key], self._units)
        except PintTypeError:
            raise
        except TypeError:
            raise TypeError(
                "Neither Quantity object nor its magnitude ({})"
                "supports indexing".format(self._magnitude)
            )

    def __setitem__(self, key, value):
        try:
            if np.ma.is_masked(value) or math.isnan(value):
                self._magnitude[key] = value
                return
        except TypeError:
            pass

        try:
            if isinstance(value, self.__class__):
                factor = self.__class__(
                    value.magnitude, value._units / self._units
                ).to_root_units()
            else:
                factor = self.__class__(value, self._units ** (-1)).to_root_units()

            if isinstance(factor, self.__class__):
                if not factor.dimensionless:
                    raise DimensionalityError(
                        value,
                        self.units,
                        extra_msg=". Assign a quantity with the same dimensionality "
                        "or access the magnitude directly as "
                        f"`obj.magnitude[{key}] = {value}`.",
                    )
                self._magnitude[key] = factor.magnitude
            else:
                self._magnitude[key] = factor

        except PintTypeError:
            raise
        except TypeError as exc:
            raise TypeError(
                f"Neither Quantity object nor its magnitude ({self._magnitude}) "
                "supports indexing"
            ) from exc

    def tolist(self):
        units = self._units
        return [
            self.__class__(value, units).tolist()
            if isinstance(value, list)
            else self.__class__(value, units)
            for value in self._magnitude.tolist()
        ]

    # Measurement support
    def plus_minus(self, error, relative=False):
        if isinstance(error, self.__class__):
            if relative:
                raise ValueError("{} is not a valid relative error.".format(error))
            error = error.to(self._units).magnitude
        else:
            if relative:
                error = error * abs(self.magnitude)

        return self._REGISTRY.Measurement(copy.copy(self.magnitude), error, self._units)

    def _get_unit_definition(self, unit: str) -> UnitDefinition:
        try:
            return self._REGISTRY._units[unit]
        except KeyError:
            # pint#1062: The __init__ method of this object added the unit to
            # UnitRegistry._units (e.g. units with prefix are added on the fly the
            # first time they're used) but the key was later removed, e.g. because
            # a Context with unit redefinitions was deactivated.
            self._REGISTRY.parse_units(unit)
            return self._REGISTRY._units[unit]

    # methods/properties that help for math operations with offset units
    @property
    def _is_multiplicative(self) -> bool:
        """Check if the Quantity object has only multiplicative units."""
        return not self._get_non_multiplicative_units()

    def _get_non_multiplicative_units(self) -> List[str]:
        """Return a list of the of non-multiplicative units of the Quantity object."""
        return [
            unit
            for unit in self._units
            if not self._get_unit_definition(unit).is_multiplicative
        ]

    def _get_delta_units(self) -> List[str]:
        """Return list of delta units ot the Quantity object."""
        return [u for u in self._units if u.startswith("delta_")]

    def _has_compatible_delta(self, unit: str) -> bool:
        """"Check if Quantity object has a delta_unit that is compatible with unit
        """
        deltas = self._get_delta_units()
        if "delta_" + unit in deltas:
            return True
        # Look for delta units with same dimension as the offset unit
        offset_unit_dim = self._get_unit_definition(unit).reference
        return any(
            self._get_unit_definition(d).reference == offset_unit_dim for d in deltas
        )

    def _ok_for_muldiv(self, no_offset_units=None):
        """Checks if Quantity object can be multiplied or divided
        """

        is_ok = True
        if no_offset_units is None:
            no_offset_units = len(self._get_non_multiplicative_units())
        if no_offset_units > 1:
            is_ok = False
        if no_offset_units == 1:
            if len(self._units) > 1:
                is_ok = False
            if (
                len(self._units) == 1
                and not self._REGISTRY.autoconvert_offset_to_baseunit
            ):
                is_ok = False
            if next(iter(self._units.values())) != 1:
                is_ok = False
        return is_ok

    def to_timedelta(self):
        return datetime.timedelta(microseconds=self.to("microseconds").magnitude)

    # Dask.array.Array ducking
    def __dask_graph__(self):
        if isinstance(self._magnitude, dask_array.Array):
            return self._magnitude.__dask_graph__()
        else:
            return None

    def __dask_keys__(self):
        return self._magnitude.__dask_keys__()

    def __dask_tokenize__(self):
        return (Quantity, self._magnitude.name, self.units)

    @property
    def __dask_optimize__(self):
        return dask_array.Array.__dask_optimize__

    @property
    def __dask_scheduler__(self):
        return dask_array.Array.__dask_scheduler__

    def __dask_postcompute__(self):
        func, args = self._magnitude.__dask_postcompute__()
        return self._dask_finalize, (func, args, self.units)

    def __dask_postpersist__(self):
        func, args = self._magnitude.__dask_postpersist__()
        return self._dask_finalize, (func, args, self.units)

    @staticmethod
    def _dask_finalize(results, func, args, units):
        values = func(results, *args)
        return Quantity(values, units)

    @check_dask_array
    def compute(self, **kwargs):
        """Compute the Dask array wrapped by pint.Quantity.

        Parameters
        ----------
        **kwargs : dict
            Any keyword arguments to pass to ``dask.compute``.

        Returns
        -------
        pint.Quantity
            A pint.Quantity wrapped numpy array.
        """
        (result,) = compute(self, **kwargs)
        return result

    @check_dask_array
    def persist(self, **kwargs):
        """Persist the Dask Array wrapped by pint.Quantity.

        Parameters
        ----------
        **kwargs : dict
            Any keyword arguments to pass to ``dask.persist``.

        Returns
        -------
        pint.Quantity
            A pint.Quantity wrapped Dask array.
        """
        (result,) = persist(self, **kwargs)
        return result

    @check_dask_array
    def visualize(self, **kwargs):
        """Produce a visual representation of the Dask graph.

        The graphviz library is required.

        Parameters
        ----------
        **kwargs : dict
            Any keyword arguments to pass to ``dask.visualize``.

        Returns
        -------

        """
        visualize(self, **kwargs)


_Quantity = Quantity


def build_quantity_class(registry):
    class Quantity(_Quantity):
        _REGISTRY = registry

    return Quantity
