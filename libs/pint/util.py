"""
    pint.util
    ~~~~~~~~~

    Miscellaneous functions for pint.

    :copyright: 2016 by Pint Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import logging
import math
import operator
import re
from collections.abc import Mapping
from fractions import Fraction
from functools import lru_cache, partial
from logging import NullHandler
from numbers import Number
from token import NAME, NUMBER

from .compat import NUMERIC_TYPES, tokenizer
from .errors import DefinitionSyntaxError
from .formatting import format_unit
from .pint_eval import build_eval_tree

logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())


def matrix_to_string(
    matrix, row_headers=None, col_headers=None, fmtfun=lambda x: str(int(x))
):
    """Takes a 2D matrix (as nested list) and returns a string.

    Parameters
    ----------
    matrix :

    row_headers :
         (Default value = None)
    col_headers :
         (Default value = None)
    fmtfun :
         (Default value = lambda x: str(int(x)))

    Returns
    -------

    """
    ret = []
    if col_headers:
        ret.append(("\t" if row_headers else "") + "\t".join(col_headers))
    if row_headers:
        ret += [
            rh + "\t" + "\t".join(fmtfun(f) for f in row)
            for rh, row in zip(row_headers, matrix)
        ]
    else:
        ret += ["\t".join(fmtfun(f) for f in row) for row in matrix]

    return "\n".join(ret)


def transpose(matrix):
    """Takes a 2D matrix (as nested list) and returns the transposed version.

    Parameters
    ----------
    matrix :


    Returns
    -------

    """
    return [list(val) for val in zip(*matrix)]


def column_echelon_form(matrix, ntype=Fraction, transpose_result=False):
    """Calculates the column echelon form using Gaussian elimination.

    Parameters
    ----------
    matrix :
        a 2D matrix as nested list.
    ntype :
        the numerical type to use in the calculation. (Default value = Fraction)
    transpose_result :
        indicates if the returned matrix should be transposed. (Default value = False)

    Returns
    -------
    type
        column echelon form, transformed identity matrix, swapped rows

    """
    lead = 0

    M = transpose(matrix)

    _transpose = transpose if transpose_result else lambda x: x

    rows, cols = len(M), len(M[0])

    new_M = []
    for row in M:
        r = []
        for x in row:
            if isinstance(x, float):
                x = ntype.from_float(x)
            else:
                x = ntype(x)
            r.append(x)
        new_M.append(r)
    M = new_M

    # M = [[ntype(x) for x in row] for row in M]
    I = [  # noqa: E741
        [ntype(1) if n == nc else ntype(0) for nc in range(rows)] for n in range(rows)
    ]
    swapped = []

    for r in range(rows):
        if lead >= cols:
            return _transpose(M), _transpose(I), swapped
        i = r
        while M[i][lead] == 0:
            i += 1
            if i != rows:
                continue
            i = r
            lead += 1
            if cols == lead:
                return _transpose(M), _transpose(I), swapped

        M[i], M[r] = M[r], M[i]
        I[i], I[r] = I[r], I[i]

        swapped.append(i)
        lv = M[r][lead]
        M[r] = [mrx / lv for mrx in M[r]]
        I[r] = [mrx / lv for mrx in I[r]]

        for i in range(rows):
            if i == r:
                continue
            lv = M[i][lead]
            M[i] = [iv - lv * rv for rv, iv in zip(M[r], M[i])]
            I[i] = [iv - lv * rv for rv, iv in zip(I[r], I[i])]

        lead += 1

    return _transpose(M), _transpose(I), swapped


def pi_theorem(quantities, registry=None):
    """Builds dimensionless quantities using the Buckingham π theorem

    Parameters
    ----------
    quantities : dict
        mapping between variable name and units
    registry :
         (Default value = None)

    Returns
    -------
    type
        a list of dimensionless quantities expressed as dicts

    """

    # Preprocess input and build the dimensionality Matrix
    quant = []
    dimensions = set()

    if registry is None:
        getdim = lambda x: x
        non_int_type = float
    else:
        getdim = registry.get_dimensionality
        non_int_type = registry.non_int_type

    for name, value in quantities.items():
        if isinstance(value, str):
            value = ParserHelper.from_string(value, non_int_type=non_int_type)
        if isinstance(value, dict):
            dims = getdim(registry.UnitsContainer(value))
        elif not hasattr(value, "dimensionality"):
            dims = getdim(value)
        else:
            dims = value.dimensionality

        if not registry and any(not key.startswith("[") for key in dims):
            logger.warning(
                "A non dimension was found and a registry was not provided. "
                "Assuming that it is a dimension name: {}.".format(dims)
            )

        quant.append((name, dims))
        dimensions = dimensions.union(dims.keys())

    dimensions = list(dimensions)

    # Calculate dimensionless  quantities
    M = [
        [dimensionality[dimension] for name, dimensionality in quant]
        for dimension in dimensions
    ]

    M, identity, pivot = column_echelon_form(M, transpose_result=False)

    # Collect results
    # Make all numbers integers and minimize the number of negative exponents.
    # Remove zeros
    results = []
    for rowm, rowi in zip(M, identity):
        if any(el != 0 for el in rowm):
            continue
        max_den = max(f.denominator for f in rowi)
        neg = -1 if sum(f < 0 for f in rowi) > sum(f > 0 for f in rowi) else 1
        results.append(
            dict(
                (q[0], neg * f.numerator * max_den / f.denominator)
                for q, f in zip(quant, rowi)
                if f.numerator != 0
            )
        )
    return results


def solve_dependencies(dependencies):
    """Solve a dependency graph.

    Parameters
    ----------
    dependencies :
        dependency dictionary. For each key, the value is an iterable indicating its
        dependencies.

    Returns
    -------
    type
        iterator of sets, each containing keys of independents tasks dependent only of
        the previous tasks in the list.

    """
    while dependencies:
        # values not in keys (items without dep)
        t = {i for v in dependencies.values() for i in v} - dependencies.keys()
        # and keys without value (items without dep)
        t.update(k for k, v in dependencies.items() if not v)
        # can be done right away
        if not t:
            raise ValueError(
                "Cyclic dependencies exist among these items: {}".format(
                    ", ".join(repr(x) for x in dependencies.items())
                )
            )
        # and cleaned up
        dependencies = {k: v - t for k, v in dependencies.items() if v}
        yield t


def find_shortest_path(graph, start, end, path=None):
    path = (path or []) + [start]
    if start == end:
        return path
    if start not in graph:
        return None
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    return shortest


def find_connected_nodes(graph, start, visited=None):
    if start not in graph:
        return None

    visited = visited or set()
    visited.add(start)

    for node in graph[start]:
        if node not in visited:
            find_connected_nodes(graph, node, visited)

    return visited


class udict(dict):
    """Custom dict implementing __missing__."""

    def __missing__(self, key):
        return 0

    def copy(self):
        return udict(self)


class UnitsContainer(Mapping):
    """The UnitsContainer stores the product of units and their respective
    exponent and implements the corresponding operations.

    UnitsContainer is a read-only mapping. All operations (even in place ones)

    Parameters
    ----------

    Returns
    -------
    type


    """

    __slots__ = ("_d", "_hash", "_one", "_non_int_type")

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], UnitsContainer):
            default_non_int_type = args[0]._non_int_type
        else:
            default_non_int_type = float

        self._non_int_type = kwargs.pop("non_int_type", default_non_int_type)

        if self._non_int_type is float:
            self._one = 1
        else:
            self._one = self._non_int_type("1")

        d = udict(*args, **kwargs)
        self._d = d
        for key, value in d.items():
            if not isinstance(key, str):
                raise TypeError("key must be a str, not {}".format(type(key)))
            if not isinstance(value, Number):
                raise TypeError("value must be a number, not {}".format(type(value)))
            if not isinstance(value, int) and not isinstance(value, self._non_int_type):
                d[key] = self._non_int_type(value)
        self._hash = None

    def copy(self):
        return self.__copy__()

    def add(self, key, value):
        newval = self._d[key] + value
        new = self.copy()
        if newval:
            new._d[key] = newval
        else:
            new._d.pop(key)
        new._hash = None
        return new

    def remove(self, keys):
        """Create a new UnitsContainer purged from given keys.

        Parameters
        ----------
        keys :


        Returns
        -------

        """
        new = self.copy()
        for k in keys:
            new._d.pop(k)
        new._hash = None
        return new

    def rename(self, oldkey, newkey):
        """Create a new UnitsContainer in which an entry has been renamed.

        Parameters
        ----------
        oldkey :

        newkey :


        Returns
        -------

        """
        new = self.copy()
        new._d[newkey] = new._d.pop(oldkey)
        new._hash = None
        return new

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d[key]

    def __contains__(self, key):
        return key in self._d

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(frozenset(self._d.items()))
        return self._hash

    # Only needed by pickle protocol 0 and 1 (used by pytables)
    def __getstate__(self):
        return self._d, self._hash, self._one, self._non_int_type

    def __setstate__(self, state):
        self._d, self._hash, self._one, self._non_int_type = state

    def __eq__(self, other):
        if isinstance(other, UnitsContainer):
            # UnitsContainer.__hash__(self) is not the same as hash(self); see
            # ParserHelper.__hash__ and __eq__.
            # Different hashes guarantee that the actual contents are different, but
            # identical hashes give no guarantee of equality.
            # e.g. in CPython, hash(-1) == hash(-2)
            if UnitsContainer.__hash__(self) != UnitsContainer.__hash__(other):
                return False
            other = other._d

        elif isinstance(other, str):
            other = ParserHelper.from_string(other, self._non_int_type)
            other = other._d

        return dict.__eq__(self._d, other)

    def __str__(self):
        return self.__format__("")

    def __repr__(self):
        tmp = "{%s}" % ", ".join(
            ["'{}': {}".format(key, value) for key, value in sorted(self._d.items())]
        )
        return "<UnitsContainer({})>".format(tmp)

    def __format__(self, spec):
        return format_unit(self, spec)

    def format_babel(self, spec, **kwspec):
        return format_unit(self, spec, **kwspec)

    def __copy__(self):
        # Skip expensive health checks performed by __init__
        out = object.__new__(self.__class__)
        out._d = self._d.copy()
        out._hash = self._hash
        out._non_int_type = self._non_int_type
        out._one = self._one
        return out

    def __mul__(self, other):
        if not isinstance(other, self.__class__):
            err = "Cannot multiply UnitsContainer by {}"
            raise TypeError(err.format(type(other)))

        new = self.copy()
        for key, value in other.items():
            new._d[key] += value
            if new._d[key] == 0:
                del new._d[key]

        new._hash = None
        return new

    __rmul__ = __mul__

    def __pow__(self, other):
        if not isinstance(other, NUMERIC_TYPES):
            err = "Cannot power UnitsContainer by {}"
            raise TypeError(err.format(type(other)))

        new = self.copy()
        for key, value in new._d.items():
            new._d[key] *= other
        new._hash = None
        return new

    def __truediv__(self, other):
        if not isinstance(other, self.__class__):
            err = "Cannot divide UnitsContainer by {}"
            raise TypeError(err.format(type(other)))

        new = self.copy()
        for key, value in other.items():
            new._d[key] -= value
            if new._d[key] == 0:
                del new._d[key]

        new._hash = None
        return new

    def __rtruediv__(self, other):
        if not isinstance(other, self.__class__) and other != 1:
            err = "Cannot divide {} by UnitsContainer"
            raise TypeError(err.format(type(other)))

        return self ** -1


class ParserHelper(UnitsContainer):
    """The ParserHelper stores in place the product of variables and
    their respective exponent and implements the corresponding operations.

    ParserHelper is a read-only mapping. All operations (even in place ones)

    Parameters
    ----------

    Returns
    -------
    type
        WARNING : The hash value used does not take into account the scale
        attribute so be careful if you use it as a dict key and then two unequal
        object can have the same hash.

    """

    __slots__ = ("scale",)

    def __init__(self, scale=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scale = scale

    @classmethod
    def from_word(cls, input_word, non_int_type=float):
        """Creates a ParserHelper object with a single variable with exponent one.

        Equivalent to: ParserHelper({'word': 1})

        Parameters
        ----------
        input_word :


        Returns
        -------

        """
        if non_int_type is float:
            return cls(1, [(input_word, 1)], non_int_type=non_int_type)
        else:
            ONE = non_int_type("1.0")
            return cls(ONE, [(input_word, ONE)], non_int_type=non_int_type)

    @classmethod
    def eval_token(cls, token, use_decimal=False, non_int_type=float):

        # TODO: remove this code when use_decimal is deprecated
        if use_decimal:
            raise DeprecationWarning(
                "`use_decimal` is deprecated, use `non_int_type` keyword argument when instantiating the registry.\n"
                ">>> from decimal import Decimal\n"
                ">>> ureg = UnitRegistry(non_int_type=Decimal)"
            )

        token_type = token.type
        token_text = token.string
        if token_type == NUMBER:
            if non_int_type is float:
                try:
                    return int(token_text)
                except ValueError:
                    return float(token_text)
            else:
                return non_int_type(token_text)
        elif token_type == NAME:
            return ParserHelper.from_word(token_text, non_int_type=non_int_type)
        else:
            raise Exception("unknown token type")

    @classmethod
    @lru_cache()
    def from_string(cls, input_string, non_int_type=float):
        """Parse linear expression mathematical units and return a quantity object.

        Parameters
        ----------
        input_string :


        Returns
        -------

        """
        if not input_string:
            return cls(non_int_type=non_int_type)

        input_string = string_preprocessor(input_string)
        if "[" in input_string:
            input_string = input_string.replace("[", "__obra__").replace(
                "]", "__cbra__"
            )
            reps = True
        else:
            reps = False

        gen = tokenizer(input_string)
        ret = build_eval_tree(gen).evaluate(
            partial(cls.eval_token, non_int_type=non_int_type)
        )

        if isinstance(ret, Number):
            return ParserHelper(ret, non_int_type=non_int_type)

        if reps:
            ret = ParserHelper(
                ret.scale,
                {
                    key.replace("__obra__", "[").replace("__cbra__", "]"): value
                    for key, value in ret.items()
                },
                non_int_type=non_int_type,
            )

        for k in list(ret):
            if k.lower() == "nan":
                del ret._d[k]
                ret.scale = math.nan

        return ret

    def __copy__(self):
        new = super().__copy__()
        new.scale = self.scale
        return new

    def copy(self):
        return self.__copy__()

    def __hash__(self):
        if self.scale != 1:
            mess = "Only scale 1 ParserHelper instance should be considered hashable"
            raise ValueError(mess)
        return super().__hash__()

    # Only needed by pickle protocol 0 and 1 (used by pytables)
    def __getstate__(self):
        return super().__getstate__() + (self.scale,)

    def __setstate__(self, state):
        super().__setstate__(state[:-1])
        self.scale = state[-1]

    def __eq__(self, other):
        if isinstance(other, ParserHelper):
            return self.scale == other.scale and super().__eq__(other)
        elif isinstance(other, str):
            return self == ParserHelper.from_string(other, self._non_int_type)
        elif isinstance(other, Number):
            return self.scale == other and not len(self._d)
        else:
            return self.scale == 1 and super().__eq__(other)

    def operate(self, items, op=operator.iadd, cleanup=True):
        d = udict(self._d)
        for key, value in items:
            d[key] = op(d[key], value)

        if cleanup:
            keys = [key for key, value in d.items() if value == 0]
            for key in keys:
                del d[key]

        return self.__class__(self.scale, d, non_int_type=self._non_int_type)

    def __str__(self):
        tmp = "{%s}" % ", ".join(
            ["'{}': {}".format(key, value) for key, value in sorted(self._d.items())]
        )
        return "{} {}".format(self.scale, tmp)

    def __repr__(self):
        tmp = "{%s}" % ", ".join(
            ["'{}': {}".format(key, value) for key, value in sorted(self._d.items())]
        )
        return "<ParserHelper({}, {})>".format(self.scale, tmp)

    def __mul__(self, other):
        if isinstance(other, str):
            new = self.add(other, self._one)
        elif isinstance(other, Number):
            new = self.copy()
            new.scale *= other
        elif isinstance(other, self.__class__):
            new = self.operate(other.items())
            new.scale *= other.scale
        else:
            new = self.operate(other.items())
        return new

    __rmul__ = __mul__

    def __pow__(self, other):
        d = self._d.copy()
        for key in self._d:
            d[key] *= other
        return self.__class__(self.scale ** other, d, non_int_type=self._non_int_type)

    def __truediv__(self, other):
        if isinstance(other, str):
            new = self.add(other, -1)
        elif isinstance(other, Number):
            new = self.copy()
            new.scale /= other
        elif isinstance(other, self.__class__):
            new = self.operate(other.items(), operator.sub)
            new.scale /= other.scale
        else:
            new = self.operate(other.items(), operator.sub)
        return new

    __floordiv__ = __truediv__

    def __rtruediv__(self, other):
        new = self.__pow__(-1)
        if isinstance(other, str):
            new = new.add(other, self._one)
        elif isinstance(other, Number):
            new.scale *= other
        elif isinstance(other, self.__class__):
            new = self.operate(other.items(), operator.add)
            new.scale *= other.scale
        else:
            new = new.operate(other.items(), operator.add)
        return new


#: List of regex substitution pairs.
_subs_re = [
    ("\N{DEGREE SIGN}", " degree"),
    (r"([\w\.\-\+\*\\\^])\s+", r"\1 "),  # merge multiple spaces
    (r"({}) squared", r"\1**2"),  # Handle square and cube
    (r"({}) cubed", r"\1**3"),
    (r"cubic ({})", r"\1**3"),
    (r"square ({})", r"\1**2"),
    (r"sq ({})", r"\1**2"),
    (
        r"\b([0-9]+\.?[0-9]*)(?=[e|E][a-zA-Z]|[a-df-zA-DF-Z])",
        r"\1*",
    ),  # Handle numberLetter for multiplication
    (r"([\w\.\-])\s+(?=\w)", r"\1*"),  # Handle space for multiplication
]

#: Compiles the regex and replace {} by a regex that matches an identifier.
_subs_re = [(re.compile(a.format(r"[_a-zA-Z][_a-zA-Z0-9]*")), b) for a, b in _subs_re]
_pretty_table = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹·⁻", "0123456789*-")
_pretty_exp_re = re.compile(r"⁻?[⁰¹²³⁴⁵⁶⁷⁸⁹]+(?:\.[⁰¹²³⁴⁵⁶⁷⁸⁹]*)?")


def string_preprocessor(input_string):
    input_string = input_string.replace(",", "")
    input_string = input_string.replace(" per ", "/")

    for a, b in _subs_re:
        input_string = a.sub(b, input_string)

    # Replace pretty format characters
    for pretty_exp in _pretty_exp_re.findall(input_string):
        exp = "**" + pretty_exp.translate(_pretty_table)
        input_string = input_string.replace(pretty_exp, exp)
    input_string = input_string.translate(_pretty_table)

    # Handle caret exponentiation
    input_string = input_string.replace("^", "**")
    return input_string


def _is_dim(name):
    return name[0] == "[" and name[-1] == "]"


class SharedRegistryObject:
    """Base class for object keeping a reference to the registree.

    Such object are for now Quantity and Unit, in a number of places it is
    that an object from this class has a '_units' attribute.

    Parameters
    ----------

    Returns
    -------

    """

    def __new__(cls, *args, **kwargs):
        inst = object.__new__(cls)
        if not hasattr(cls, "_REGISTRY"):
            # Base class, not subclasses dynamically by
            # UnitRegistry._init_dynamic_classes
            from . import _APP_REGISTRY

            inst._REGISTRY = _APP_REGISTRY
        return inst

    def _check(self, other):
        """Check if the other object use a registry and if so that it is the
        same registry.

        Parameters
        ----------
        other :


        Returns
        -------
        type
            other don't use a registry and raise ValueError if other don't use the
            same unit registry.

        """
        if self._REGISTRY is getattr(other, "_REGISTRY", None):
            return True

        elif isinstance(other, SharedRegistryObject):
            mess = "Cannot operate with {} and {} of different registries."
            raise ValueError(
                mess.format(self.__class__.__name__, other.__class__.__name__)
            )
        else:
            return False


class PrettyIPython:
    """Mixin to add pretty-printers for IPython"""

    def _repr_html_(self):
        if "~" in self.default_format:
            return "{:~H}".format(self)
        else:
            return "{:H}".format(self)

    def _repr_latex_(self):
        if "~" in self.default_format:
            return "${:~L}$".format(self)
        else:
            return "${:L}$".format(self)

    def _repr_pretty_(self, p, cycle):
        if "~" in self.default_format:
            p.text("{:~P}".format(self))
        else:
            p.text("{:P}".format(self))


def to_units_container(unit_like, registry=None):
    """Convert a unit compatible type to a UnitsContainer.

    Parameters
    ----------
    unit_like :

    registry :
         (Default value = None)

    Returns
    -------

    """
    mro = type(unit_like).mro()
    if UnitsContainer in mro:
        return unit_like
    elif SharedRegistryObject in mro:
        return unit_like._units
    elif str in mro:
        if registry:
            return registry._parse_units(unit_like)
        else:
            return ParserHelper.from_string(unit_like)
    elif dict in mro:
        if registry:
            return registry.UnitsContainer(unit_like)
        else:
            return UnitsContainer(unit_like)


def infer_base_unit(q):
    """

    Parameters
    ----------
    q :


    Returns
    -------
    type


    """
    d = udict()
    for unit_name, power in q._units.items():
        candidates = q._REGISTRY.parse_unit_name(unit_name)
        assert len(candidates) == 1
        _, base_unit, _ = candidates[0]
        d[base_unit] += power

    # remove values that resulted in a power of 0
    return UnitsContainer({k: v for k, v in d.items() if v != 0})


def getattr_maybe_raise(self, item):
    """Helper function invoked at start of all overridden ``__getattr__``.

    Raise AttributeError if the user tries to ask for a _ or __ attribute,
    *unless* it is immediately followed by a number, to enable units
    encompassing constants, such as ``L / _100km``.

    Parameters
    ----------
    item : string
        Item to be found.


    Returns
    -------

    """
    # Double-underscore attributes are tricky to detect because they are
    # automatically prefixed with the class name - which may be a subclass of self
    if (
        item.endswith("__")
        or len(item.lstrip("_")) == 0
        or (item.startswith("_") and not item.lstrip("_")[0].isdigit())
    ):
        raise AttributeError("%r object has no attribute %r" % (self, item))


class SourceIterator:
    """Iterator to facilitate reading the definition files.

    Accepts any sequence (like a list of lines, a file or another SourceIterator)

    The iterator yields the line number and line (skipping comments and empty lines)
    and stripping white spaces.

    for lineno, line in SourceIterator(sequence):
        # do something here

    """

    def __new__(cls, sequence):
        if isinstance(sequence, SourceIterator):
            return sequence

        obj = object.__new__(cls)

        if sequence is not None:
            obj.internal = enumerate(sequence, 1)
            obj.last = (None, None)

        return obj

    def __iter__(self):
        return self

    def __next__(self):
        line = ""
        while not line or line.startswith("#"):
            lineno, line = next(self.internal)
            line = line.split("#", 1)[0].strip()

        self.last = lineno, line
        return lineno, line

    next = __next__

    def block_iter(self):
        """Iterate block including header."""
        return BlockIterator(self)


class BlockIterator(SourceIterator):
    """Like SourceIterator but stops when it finds '@end'
    It also raises an error if another '@' directive is found inside.
    """

    def __new__(cls, line_iterator):
        obj = SourceIterator.__new__(cls, None)
        obj.internal = line_iterator.internal
        obj.last = line_iterator.last
        obj.done_last = False
        return obj

    def __next__(self):
        if not self.done_last:
            self.done_last = True
            return self.last

        lineno, line = SourceIterator.__next__(self)
        if line.startswith("@end"):
            raise StopIteration
        elif line.startswith("@"):
            raise DefinitionSyntaxError("cannot nest @ directives", lineno=lineno)

        return lineno, line

    next = __next__


def iterable(y):
    """Check whether or not an object can be iterated over.

    Vendored from numpy under the terms of the BSD 3-Clause License. (Copyright
    (c) 2005-2019, NumPy Developers.)

    Parameters
    ----------
    value :
        Input object.
    type :
        object
    y :

    """
    try:
        iter(y)
    except TypeError:
        return False
    return True


def sized(y):
    """Check whether or not an object has a defined length.

    Parameters
    ----------
    value :
        Input object.
    type :
        object
    y :

    """
    try:
        len(y)
    except TypeError:
        return False
    return True
