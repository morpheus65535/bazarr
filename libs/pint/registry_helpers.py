"""
    pint.registry_helpers
    ~~~~~~~~~~~~~~~~~~~~~

    Miscellaneous methods of the registry writen as separate functions.

    :copyright: 2016 by Pint Authors, see AUTHORS for more details..
    :license: BSD, see LICENSE for more details.
"""

import functools
from inspect import signature
from itertools import zip_longest

from .errors import DimensionalityError
from .util import UnitsContainer, to_units_container


def _replace_units(original_units, values_by_name):
    """Convert a unit compatible type to a UnitsContainer.

    Parameters
    ----------
    original_units :
        a UnitsContainer instance.
    values_by_name :
        a map between original names and the new values.

    Returns
    -------

    """
    q = 1
    for arg_name, exponent in original_units.items():
        q = q * values_by_name[arg_name] ** exponent

    return getattr(q, "_units", UnitsContainer({}))


def _to_units_container(a, registry=None):
    """Convert a unit compatible type to a UnitsContainer,
    checking if it is string field prefixed with an equal
    (which is considered a reference)

    Parameters
    ----------
    a :

    registry :
         (Default value = None)

    Returns
    -------
    UnitsContainer, bool


    """
    if isinstance(a, str) and "=" in a:
        return to_units_container(a.split("=", 1)[1]), True
    return to_units_container(a, registry), False


def _parse_wrap_args(args, registry=None):

    # Arguments which contain definitions
    # (i.e. names that appear alone and for the first time)
    defs_args = set()
    defs_args_ndx = set()

    # Arguments which depend on others
    dependent_args_ndx = set()

    # Arguments which have units.
    unit_args_ndx = set()

    # _to_units_container
    args_as_uc = [_to_units_container(arg, registry) for arg in args]

    # Check for references in args, remove None values
    for ndx, (arg, is_ref) in enumerate(args_as_uc):
        if arg is None:
            continue
        elif is_ref:
            if len(arg) == 1:
                [(key, value)] = arg.items()
                if value == 1 and key not in defs_args:
                    # This is the first time that
                    # a variable is used => it is a definition.
                    defs_args.add(key)
                    defs_args_ndx.add(ndx)
                    args_as_uc[ndx] = (key, True)
                else:
                    # The variable was already found elsewhere,
                    # we consider it a dependent variable.
                    dependent_args_ndx.add(ndx)
            else:
                dependent_args_ndx.add(ndx)
        else:
            unit_args_ndx.add(ndx)

    # Check that all valid dependent variables
    for ndx in dependent_args_ndx:
        arg, is_ref = args_as_uc[ndx]
        if not isinstance(arg, dict):
            continue
        if not set(arg.keys()) <= defs_args:
            raise ValueError(
                "Found a missing token while wrapping a function: "
                "Not all variable referenced in %s are defined using !" % args[ndx]
            )

    def _converter(ureg, values, strict):
        new_values = list(value for value in values)

        values_by_name = {}

        # first pass: Grab named values
        for ndx in defs_args_ndx:
            value = values[ndx]
            values_by_name[args_as_uc[ndx][0]] = value
            new_values[ndx] = getattr(value, "_magnitude", value)

        # second pass: calculate derived values based on named values
        for ndx in dependent_args_ndx:
            value = values[ndx]
            assert _replace_units(args_as_uc[ndx][0], values_by_name) is not None
            new_values[ndx] = ureg._convert(
                getattr(value, "_magnitude", value),
                getattr(value, "_units", UnitsContainer({})),
                _replace_units(args_as_uc[ndx][0], values_by_name),
            )

        # third pass: convert other arguments
        for ndx in unit_args_ndx:

            if isinstance(values[ndx], ureg.Quantity):
                new_values[ndx] = ureg._convert(
                    values[ndx]._magnitude, values[ndx]._units, args_as_uc[ndx][0]
                )
            else:
                if strict:
                    if isinstance(values[ndx], str):
                        # if the value is a string, we try to parse it
                        tmp_value = ureg.parse_expression(values[ndx])
                        new_values[ndx] = ureg._convert(
                            tmp_value._magnitude, tmp_value._units, args_as_uc[ndx][0]
                        )
                    else:
                        raise ValueError(
                            "A wrapped function using strict=True requires "
                            "quantity or a string for all arguments with not None units. "
                            "(error found for {}, {})".format(
                                args_as_uc[ndx][0], new_values[ndx]
                            )
                        )

        return new_values, values_by_name

    return _converter


def _apply_defaults(func, args, kwargs):
    """Apply default keyword arguments.

    Named keywords may have been left blank. This function applies the default
    values so that every argument is defined.
    """

    sig = signature(func)
    bound_arguments = sig.bind(*args, **kwargs)
    for param in sig.parameters.values():
        if param.name not in bound_arguments.arguments:
            bound_arguments.arguments[param.name] = param.default
    args = [bound_arguments.arguments[key] for key in sig.parameters.keys()]
    return args, {}


def wraps(ureg, ret, args, strict=True):
    """Wraps a function to become pint-aware.

    Use it when a function requires a numerical value but in some specific
    units. The wrapper function will take a pint quantity, convert to the units
    specified in `args` and then call the wrapped function with the resulting
    magnitude.

    The value returned by the wrapped function will be converted to the units
    specified in `ret`.

    Parameters
    ----------
    ureg : pint.UnitRegistry
        a UnitRegistry instance.
    ret : str, pint.Unit, iterable of str, or iterable of pint.Unit
        Units of each of the return values. Use `None` to skip argument conversion.
    args : str, pint.Unit, iterable of str, or iterable of pint.Unit
        Units of each of the input arguments. Use `None` to skip argument conversion.
    strict : bool
        Indicates that only quantities are accepted. (Default value = True)

    Returns
    -------
    callable
        the wrapper function.

    Raises
    ------
    TypeError
        if the number of given arguments does not match the number of function parameters.
        if the any of the provided arguments is not a unit a string or Quantity

    """

    if not isinstance(args, (list, tuple)):
        args = (args,)

    for arg in args:
        if arg is not None and not isinstance(arg, (ureg.Unit, str)):
            raise TypeError(
                "wraps arguments must by of type str or Unit, not %s (%s)"
                % (type(arg), arg)
            )

    converter = _parse_wrap_args(args)

    is_ret_container = isinstance(ret, (list, tuple))
    if is_ret_container:
        for arg in ret:
            if arg is not None and not isinstance(arg, (ureg.Unit, str)):
                raise TypeError(
                    "wraps 'ret' argument must by of type str or Unit, not %s (%s)"
                    % (type(arg), arg)
                )
        ret = ret.__class__([_to_units_container(arg, ureg) for arg in ret])
    else:
        if ret is not None and not isinstance(ret, (ureg.Unit, str)):
            raise TypeError(
                "wraps 'ret' argument must by of type str or Unit, not %s (%s)"
                % (type(ret), ret)
            )
        ret = _to_units_container(ret, ureg)

    def decorator(func):

        count_params = len(signature(func).parameters)
        if len(args) != count_params:
            raise TypeError(
                "%s takes %i parameters, but %i units were passed"
                % (func.__name__, count_params, len(args))
            )

        assigned = tuple(
            attr for attr in functools.WRAPPER_ASSIGNMENTS if hasattr(func, attr)
        )
        updated = tuple(
            attr for attr in functools.WRAPPER_UPDATES if hasattr(func, attr)
        )

        @functools.wraps(func, assigned=assigned, updated=updated)
        def wrapper(*values, **kw):

            values, kw = _apply_defaults(func, values, kw)

            # In principle, the values are used as is
            # When then extract the magnitudes when needed.
            new_values, values_by_name = converter(ureg, values, strict)

            result = func(*new_values, **kw)

            if is_ret_container:
                out_units = (
                    _replace_units(r, values_by_name) if is_ref else r
                    for (r, is_ref) in ret
                )
                return ret.__class__(
                    res if unit is None else ureg.Quantity(res, unit)
                    for unit, res in zip_longest(out_units, result)
                )

            if ret[0] is None:
                return result

            return ureg.Quantity(
                result, _replace_units(ret[0], values_by_name) if ret[1] else ret[0]
            )

        return wrapper

    return decorator


def check(ureg, *args):
    """Decorator to for quantity type checking for function inputs.

    Use it to ensure that the decorated function input parameters match
    the expected dimension of pint quantity.

    The wrapper function raises:
      - `pint.DimensionalityError` if an argument doesn't match the required dimensions.

    ureg : UnitRegistry
        a UnitRegistry instance.
    args : str or UnitContainer or None
        Dimensions of each of the input arguments.
        Use `None` to skip argument conversion.

    Returns
    -------
    callable
        the wrapped function.

    Raises
    ------
    TypeError
        If the number of given dimensions does not match the number of function
        parameters.
    ValueError
        If the any of the provided dimensions cannot be parsed as a dimension.
    """
    dimensions = [
        ureg.get_dimensionality(dim) if dim is not None else None for dim in args
    ]

    def decorator(func):

        count_params = len(signature(func).parameters)
        if len(dimensions) != count_params:
            raise TypeError(
                "%s takes %i parameters, but %i dimensions were passed"
                % (func.__name__, count_params, len(dimensions))
            )

        assigned = tuple(
            attr for attr in functools.WRAPPER_ASSIGNMENTS if hasattr(func, attr)
        )
        updated = tuple(
            attr for attr in functools.WRAPPER_UPDATES if hasattr(func, attr)
        )

        @functools.wraps(func, assigned=assigned, updated=updated)
        def wrapper(*args, **kwargs):
            list_args, empty = _apply_defaults(func, args, kwargs)

            for dim, value in zip(dimensions, list_args):

                if dim is None:
                    continue

                if not ureg.Quantity(value).check(dim):
                    val_dim = ureg.get_dimensionality(value)
                    raise DimensionalityError(value, "a quantity of", val_dim, dim)
            return func(*args, **kwargs)

        return wrapper

    return decorator
