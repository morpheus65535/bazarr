"""
pint.registry
~~~~~~~~~~~~~

Defines the Registry, a class to contain units and their relations.

The module actually defines 5 registries with different capabilites:

- BaseRegistry: Basic unit definition and querying.
                Conversion between multiplicative units.

- NonMultiplicativeRegistry: Conversion between non multiplicative (offset) units.
                             (e.g. Temperature)

  * Inherits from BaseRegistry

- ContextRegisty: Conversion between units with different dimensions according
                  to previously established relations (contexts) - e.g. in spectroscopy,
                  conversion between frequency and energy is possible. May also override
                  conversions between units on the same dimension - e.g. different
                  rounding conventions.

  * Inherits from BaseRegistry

- SystemRegistry: Group unit and changing of base units.
                  (e.g. in MKS, meter, kilogram and second are base units.)

  * Inherits from BaseRegistry

- UnitRegistry: Combine all previous capabilities, it is exposed by Pint.

:copyright: 2016 by Pint Authors, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import copy
import functools
import itertools
import locale
import os
import re
from collections import ChainMap, defaultdict
from contextlib import contextmanager
from decimal import Decimal
from fractions import Fraction
from io import StringIO
from tokenize import NAME, NUMBER

from . import registry_helpers, systems
from .compat import babel_parse, tokenizer
from .context import Context, ContextChain
from .converters import LogarithmicConverter, ScaleConverter
from .definitions import (
    AliasDefinition,
    Definition,
    DimensionDefinition,
    PrefixDefinition,
    UnitDefinition,
)
from .errors import (
    DefinitionSyntaxError,
    DimensionalityError,
    RedefinitionError,
    UndefinedUnitError,
)
from .pint_eval import build_eval_tree
from .util import (
    ParserHelper,
    SourceIterator,
    UnitsContainer,
    _is_dim,
    find_connected_nodes,
    find_shortest_path,
    getattr_maybe_raise,
    logger,
    pi_theorem,
    solve_dependencies,
    string_preprocessor,
    to_units_container,
)

try:
    import importlib.resources as importlib_resources
except ImportError:
    # Backport for Python < 3.7
    import importlib_resources


_BLOCK_RE = re.compile(r" |\(")


@functools.lru_cache()
def pattern_to_regex(pattern):
    if hasattr(pattern, "finditer"):
        pattern = pattern.pattern

    # Replace "{unit_name}" match string with float regex with unit_name as group
    pattern = re.sub(
        r"{(\w+)}", r"(?P<\1>[+-]?[0-9]+(?:.[0-9]+)?(?:[Ee][+-]?[0-9]+)?)", pattern
    )

    return re.compile(pattern)


class RegistryMeta(type):
    """This is just to call after_init at the right time
    instead of asking the developer to do it when subclassing.
    """

    def __call__(self, *args, **kwargs):
        obj = super().__call__(*args, **kwargs)
        obj._after_init()
        return obj


class RegistryCache:
    """Cache to speed up unit registries"""

    def __init__(self):
        #: Maps dimensionality (UnitsContainer) to Units (str)
        self.dimensional_equivalents = {}
        #: Maps dimensionality (UnitsContainer) to Dimensionality (UnitsContainer)
        self.root_units = {}
        #: Maps dimensionality (UnitsContainer) to Units (UnitsContainer)
        self.dimensionality = {}
        #: Cache the unit name associated to user input. ('mV' -> 'millivolt')
        self.parse_unit = {}


class ContextCacheOverlay:
    """Layer on top of the base UnitRegistry cache, specific to a combination of
    active contexts which contain unit redefinitions.
    """

    def __init__(self, registry_cache: RegistryCache):
        self.dimensional_equivalents = registry_cache.dimensional_equivalents
        self.root_units = {}
        self.dimensionality = registry_cache.dimensionality
        self.parse_unit = registry_cache.parse_unit


class BaseRegistry(metaclass=RegistryMeta):
    """Base class for all registries.

    Capabilities:

    - Register units, prefixes, and dimensions, and their relations.
    - Convert between units.
    - Find dimensionality of a unit.
    - Parse units with prefix and/or suffix.
    - Parse expressions.
    - Parse a definition file.
    - Allow extending the definition file parser by registering @ directives.

    Parameters
    ----------
    filename : str or None
        path of the units definition file to load or line iterable object. Empty to load
        the default definition file. None to leave the UnitRegistry empty.
    force_ndarray : bool
        convert any input, scalar or not to a numpy.ndarray.
    force_ndarray_like : bool
        convert all inputs other than duck arrays to a numpy.ndarray.
    on_redefinition : str
        action to take in case a unit is redefined: 'warn', 'raise', 'ignore'
    auto_reduce_dimensions :
        If True, reduce dimensionality on appropriate operations.
    preprocessors :
        list of callables which are iteratively ran on any input expression or unit
        string
    fmt_locale :
        locale identifier string, used in `format_babel`
    non_int_type : type
        numerical type used for non integer values. (Default: float)
    case_sensitive : bool, optional
        Control default case sensitivity of unit parsing. (Default: True)

    """

    #: Map context prefix to function
    #: type: Dict[str, (SourceIterator -> None)]
    _parsers = None

    #: Babel.Locale instance or None
    fmt_locale = None

    def __init__(
        self,
        filename="",
        force_ndarray=False,
        force_ndarray_like=False,
        on_redefinition="warn",
        auto_reduce_dimensions=False,
        preprocessors=None,
        fmt_locale=None,
        non_int_type=float,
        case_sensitive=True,
    ):
        self._register_parsers()
        self._init_dynamic_classes()

        self._filename = filename
        self.force_ndarray = force_ndarray
        self.force_ndarray_like = force_ndarray_like
        self.preprocessors = preprocessors or []

        #: Action to take in case a unit is redefined. 'warn', 'raise', 'ignore'
        self._on_redefinition = on_redefinition

        #: Determines if dimensionality should be reduced on appropriate operations.
        self.auto_reduce_dimensions = auto_reduce_dimensions

        #: Default locale identifier string, used when calling format_babel without explicit locale.
        self.set_fmt_locale(fmt_locale)

        #: Numerical type used for non integer values.
        self.non_int_type = non_int_type

        #: Default unit case sensitivity
        self.case_sensitive = case_sensitive

        #: Map between name (string) and value (string) of defaults stored in the
        #: definitions file.
        self._defaults = {}

        #: Map dimension name (string) to its definition (DimensionDefinition).
        self._dimensions = {}

        #: Map unit name (string) to its definition (UnitDefinition).
        #: Might contain prefixed units.
        self._units = {}

        #: Map unit name in lower case (string) to a set of unit names with the right
        #: case.
        #: Does not contain prefixed units.
        #: e.g: 'hz' - > set('Hz', )
        self._units_casei = defaultdict(set)

        #: Map prefix name (string) to its definition (PrefixDefinition).
        self._prefixes = {"": PrefixDefinition("", "", (), 1)}

        #: Map suffix name (string) to canonical , and unit alias to canonical unit name
        self._suffixes = {"": "", "s": ""}

        #: Map contexts to RegistryCache
        self._cache = RegistryCache()

        self._initialized = False

    def _init_dynamic_classes(self):
        """Generate subclasses on the fly and attach them to self"""
        from .unit import build_unit_class

        self.Unit = build_unit_class(self)

        from .quantity import build_quantity_class

        self.Quantity = build_quantity_class(self)

        from .measurement import build_measurement_class

        self.Measurement = build_measurement_class(self)

    def _after_init(self):
        """This should be called after all __init__"""

        if self._filename == "":
            self.load_definitions("default_en.txt", True)
        elif self._filename is not None:
            self.load_definitions(self._filename)

        self._build_cache()
        self._initialized = True

    def _register_parsers(self):
        self._register_parser("@defaults", self._parse_defaults)

    def _parse_defaults(self, ifile):
        """Loader for a @default section.
        """
        next(ifile)
        for lineno, part in ifile.block_iter():
            k, v = part.split("=")
            self._defaults[k.strip()] = v.strip()

    def __deepcopy__(self, memo):
        new = object.__new__(type(self))
        new.__dict__ = copy.deepcopy(self.__dict__, memo)
        new._init_dynamic_classes()
        return new

    def __getattr__(self, item):
        getattr_maybe_raise(self, item)
        return self.Unit(item)

    def __getitem__(self, item):
        logger.warning(
            "Calling the getitem method from a UnitRegistry is deprecated. "
            "use `parse_expression` method or use the registry as a callable."
        )
        return self.parse_expression(item)

    def __contains__(self, item):
        """Support checking prefixed units with the `in` operator
        """
        try:
            self.__getattr__(item)
            return True
        except UndefinedUnitError:
            return False

    def __dir__(self):
        #: Calling dir(registry) gives all units, methods, and attributes.
        #: Also used for autocompletion in IPython.
        return list(self._units.keys()) + list(object.__dir__(self))

    def __iter__(self):
        """Allows for listing all units in registry with `list(ureg)`.

        Returns
        -------
        Iterator over names of all units in registry, ordered alphabetically.
        """
        return iter(sorted(self._units.keys()))

    def set_fmt_locale(self, loc):
        """Change the locale used by default by `format_babel`.

        Parameters
        ----------
        loc : str or None
            None` (do not translate), 'sys' (detect the system locale) or a locale id string.
        """
        if isinstance(loc, str):
            if loc == "sys":
                loc = locale.getdefaultlocale()[0]

            # We call babel parse to fail here and not in the formatting operation
            babel_parse(loc)

        self.fmt_locale = loc

    def UnitsContainer(self, *args, **kwargs):
        return UnitsContainer(*args, non_int_type=self.non_int_type, **kwargs)

    @property
    def default_format(self):
        """Default formatting string for quantities."""
        return self.Quantity.default_format

    @default_format.setter
    def default_format(self, value):
        self.Unit.default_format = value
        self.Quantity.default_format = value

    def define(self, definition):
        """Add unit to the registry.

        Parameters
        ----------
        definition : str or Definition
            a dimension, unit or prefix definition.
        """

        if isinstance(definition, str):
            for line in definition.split("\n"):
                self._define(Definition.from_string(line, self.non_int_type))
        else:
            self._define(definition)

    def _define(self, definition):
        """Add unit to the registry.

        This method defines only multiplicative units, converting any other type
        to `delta_` units.

        Parameters
        ----------
        definition : Definition
            a dimension, unit or prefix definition.

        Returns
        -------
        Definition, dict, dict
            Definition instance, case sensitive unit dict, case insensitive unit dict.

        """

        if isinstance(definition, DimensionDefinition):
            d, di = self._dimensions, None

        elif isinstance(definition, UnitDefinition):
            d, di = self._units, self._units_casei

            # For a base units, we need to define the related dimension
            # (making sure there is only one to define)
            if definition.is_base:
                for dimension in definition.reference.keys():
                    if dimension in self._dimensions:
                        if dimension != "[]":
                            raise DefinitionSyntaxError(
                                "Only one unit per dimension can be a base unit"
                            )
                        continue

                    self.define(
                        DimensionDefinition(dimension, "", (), None, is_base=True)
                    )

        elif isinstance(definition, PrefixDefinition):
            d, di = self._prefixes, None

        elif isinstance(definition, AliasDefinition):
            d, di = self._units, self._units_casei
            self._define_alias(definition, d, di)
            return d[definition.name], d, di

        else:
            raise TypeError("{} is not a valid definition.".format(definition))

        # define "delta_" units for units with an offset
        if getattr(definition.converter, "offset", 0) != 0:

            if definition.name.startswith("["):
                d_name = "[delta_" + definition.name[1:]
            else:
                d_name = "delta_" + definition.name

            if definition.symbol:
                d_symbol = "Δ" + definition.symbol
            else:
                d_symbol = None

            d_aliases = tuple("Δ" + alias for alias in definition.aliases) + tuple(
                "delta_" + alias for alias in definition.aliases
            )

            d_reference = self.UnitsContainer(
                {ref: value for ref, value in definition.reference.items()}
            )

            d_def = UnitDefinition(
                d_name,
                d_symbol,
                d_aliases,
                ScaleConverter(definition.converter.scale),
                d_reference,
                definition.is_base,
            )
        else:
            d_def = definition

        self._define_adder(d_def, d, di)

        return definition, d, di

    def _define_adder(self, definition, unit_dict, casei_unit_dict):
        """Helper function to store a definition in the internal dictionaries.
        It stores the definition under its name, symbol and aliases.
        """
        self._define_single_adder(
            definition.name, definition, unit_dict, casei_unit_dict
        )

        if definition.has_symbol:
            self._define_single_adder(
                definition.symbol, definition, unit_dict, casei_unit_dict
            )

        for alias in definition.aliases:
            if " " in alias:
                logger.warn("Alias cannot contain a space: " + alias)

            self._define_single_adder(alias, definition, unit_dict, casei_unit_dict)

    def _define_single_adder(self, key, value, unit_dict, casei_unit_dict):
        """Helper function to store a definition in the internal dictionaries.

        It warns or raise error on redefinition.
        """
        if key in unit_dict:
            if self._on_redefinition == "raise":
                raise RedefinitionError(key, type(value))
            elif self._on_redefinition == "warn":
                logger.warning("Redefining '%s' (%s)" % (key, type(value)))

        unit_dict[key] = value
        if casei_unit_dict is not None:
            casei_unit_dict[key.lower()].add(key)

    def _define_alias(self, definition, unit_dict, casei_unit_dict):
        unit = unit_dict[definition.name]
        unit.add_aliases(*definition.aliases)
        for alias in unit.aliases:
            unit_dict[alias] = unit
            casei_unit_dict[alias.lower()].add(alias)

    def _register_parser(self, prefix, parserfunc):
        """Register a loader for a given @ directive..

        Parameters
        ----------
        prefix :
            string identifying the section (e.g. @context)
        parserfunc : SourceIterator -> None
            A function that is able to parse a Definition section.

        Returns
        -------

        """
        if self._parsers is None:
            self._parsers = {}

        if prefix and prefix[0] == "@":
            self._parsers[prefix] = parserfunc
        else:
            raise ValueError("Prefix directives must start with '@'")

    def load_definitions(self, file, is_resource=False):
        """Add units and prefixes defined in a definition text file.

        Parameters
        ----------
        file :
            can be a filename or a line iterable.
        is_resource :
            used to indicate that the file is a resource file
            and therefore should be loaded from the package. (Default value = False)

        Returns
        -------

        """
        # Permit both filenames and line-iterables
        if isinstance(file, str):
            try:
                if is_resource:
                    rbytes = importlib_resources.read_binary(__package__, file)
                    return self.load_definitions(
                        StringIO(rbytes.decode("utf-8")), is_resource
                    )
                else:
                    with open(file, encoding="utf-8") as fp:
                        return self.load_definitions(fp, is_resource)
            except (RedefinitionError, DefinitionSyntaxError) as e:
                if e.filename is None:
                    e.filename = file
                raise e
            except Exception as e:
                msg = getattr(e, "message", "") or str(e)
                raise ValueError("While opening {}\n{}".format(file, msg))

        ifile = SourceIterator(file)
        for no, line in ifile:
            if line.startswith("@") and not line.startswith("@alias"):
                if line.startswith("@import"):
                    if is_resource:
                        path = line[7:].strip()
                    else:
                        try:
                            path = os.path.dirname(file.name)
                        except AttributeError:
                            path = os.getcwd()
                        path = os.path.join(path, os.path.normpath(line[7:].strip()))
                    self.load_definitions(path, is_resource)
                else:
                    parts = _BLOCK_RE.split(line)

                    loader = (
                        self._parsers.get(parts[0], None) if self._parsers else None
                    )

                    if loader is None:
                        raise DefinitionSyntaxError(
                            "Unknown directive %s" % line, lineno=no
                        )

                    try:
                        loader(ifile)
                    except DefinitionSyntaxError as ex:
                        if ex.lineno is None:
                            ex.lineno = no
                        raise ex
            else:
                try:
                    self.define(Definition.from_string(line, self.non_int_type))
                except DefinitionSyntaxError as ex:
                    if ex.lineno is None:
                        ex.lineno = no
                    raise ex
                except Exception as ex:
                    logger.error("In line {}, cannot add '{}' {}".format(no, line, ex))

    def _build_cache(self):
        """Build a cache of dimensionality and base units."""
        self._cache = RegistryCache()

        deps = {
            name: definition.reference.keys() if definition.reference else set()
            for name, definition in self._units.items()
        }

        for unit_names in solve_dependencies(deps):
            for unit_name in unit_names:
                if "[" in unit_name:
                    continue
                parsed_names = self.parse_unit_name(unit_name)
                if parsed_names:
                    prefix, base_name, _ = parsed_names[0]
                else:
                    prefix, base_name = "", unit_name

                try:
                    uc = ParserHelper.from_word(base_name, self.non_int_type)

                    bu = self._get_root_units(uc)
                    di = self._get_dimensionality(uc)

                    self._cache.root_units[uc] = bu
                    self._cache.dimensionality[uc] = di

                    if not prefix:
                        dimeq_set = self._cache.dimensional_equivalents.setdefault(
                            di, set()
                        )
                        dimeq_set.add(self._units[base_name]._name)

                except Exception as exc:
                    logger.warning(f"Could not resolve {unit_name}: {exc!r}")

    def get_name(self, name_or_alias, case_sensitive=None):
        """Return the canonical name of a unit.
        """

        if name_or_alias == "dimensionless":
            return ""

        try:
            return self._units[name_or_alias]._name
        except KeyError:
            pass

        candidates = self.parse_unit_name(name_or_alias, case_sensitive)
        if not candidates:
            raise UndefinedUnitError(name_or_alias)
        elif len(candidates) == 1:
            prefix, unit_name, _ = candidates[0]
        else:
            logger.warning(
                "Parsing {} yield multiple results. "
                "Options are: {}".format(name_or_alias, candidates)
            )
            prefix, unit_name, _ = candidates[0]

        if prefix:
            name = prefix + unit_name
            symbol = self.get_symbol(name, case_sensitive)
            prefix_def = self._prefixes[prefix]
            self._units[name] = UnitDefinition(
                name,
                symbol,
                (),
                prefix_def.converter,
                self.UnitsContainer({unit_name: 1}),
            )
            return prefix + unit_name

        return unit_name

    def get_symbol(self, name_or_alias, case_sensitive=None):
        """Return the preferred alias for a unit.
        """
        candidates = self.parse_unit_name(name_or_alias, case_sensitive)
        if not candidates:
            raise UndefinedUnitError(name_or_alias)
        elif len(candidates) == 1:
            prefix, unit_name, _ = candidates[0]
        else:
            logger.warning(
                "Parsing {0} yield multiple results. "
                "Options are: {1!r}".format(name_or_alias, candidates)
            )
            prefix, unit_name, _ = candidates[0]

        return self._prefixes[prefix].symbol + self._units[unit_name].symbol

    def _get_symbol(self, name):
        return self._units[name].symbol

    def get_dimensionality(self, input_units):
        """Convert unit or dict of units or dimensions to a dict of base dimensions
        dimensions
        """

        # TODO: This should be to_units_container(input_units, self)
        # but this tries to reparse and fail for dimensions.
        input_units = to_units_container(input_units)

        return self._get_dimensionality(input_units)

    def _get_dimensionality(self, input_units):
        """Convert a UnitsContainer to base dimensions.
        """
        if not input_units:
            return self.UnitsContainer()

        cache = self._cache.dimensionality

        try:
            return cache[input_units]
        except KeyError:
            pass

        accumulator = defaultdict(int)
        self._get_dimensionality_recurse(input_units, 1, accumulator)

        if "[]" in accumulator:
            del accumulator["[]"]

        dims = self.UnitsContainer({k: v for k, v in accumulator.items() if v != 0})

        cache[input_units] = dims

        return dims

    def _get_dimensionality_recurse(self, ref, exp, accumulator):
        for key in ref:
            exp2 = exp * ref[key]
            if _is_dim(key):
                reg = self._dimensions[key]
                if reg.is_base:
                    accumulator[key] += exp2
                elif reg.reference is not None:
                    self._get_dimensionality_recurse(reg.reference, exp2, accumulator)
            else:
                reg = self._units[self.get_name(key)]
                if reg.reference is not None:
                    self._get_dimensionality_recurse(reg.reference, exp2, accumulator)

    def _get_dimensionality_ratio(self, unit1, unit2):
        """Get the exponential ratio between two units, i.e. solve unit2 = unit1**x for x.

        Parameters
        ----------
        unit1 : UnitsContainer compatible (str, Unit, UnitsContainer, dict)
            first unit
        unit2 : UnitsContainer compatible (str, Unit, UnitsContainer, dict)
            second unit

        Returns
        -------
        number or None
            exponential proportionality or None if the units cannot be converted

        """
        # shortcut in case of equal units
        if unit1 == unit2:
            return 1

        dim1, dim2 = (self.get_dimensionality(unit) for unit in (unit1, unit2))
        if not dim1 or not dim2 or dim1.keys() != dim2.keys():  # not comparable
            return None

        ratios = (dim2[key] / val for key, val in dim1.items())
        first = next(ratios)
        if all(r == first for r in ratios):  # all are same, we're good
            return first
        return None

    def get_root_units(self, input_units, check_nonmult=True):
        """Convert unit or dict of units to the root units.

        If any unit is non multiplicative and check_converter is True,
        then None is returned as the multiplicative factor.

        Parameters
        ----------
        input_units : UnitsContainer or str
            units
        check_nonmult : bool
            if True, None will be returned as the
            multiplicative factor if a non-multiplicative
            units is found in the final Units. (Default value = True)

        Returns
        -------
        Number, pint.Unit
            multiplicative factor, base units

        """
        input_units = to_units_container(input_units, self)

        f, units = self._get_root_units(input_units, check_nonmult)

        return f, self.Unit(units)

    def _get_root_units(self, input_units, check_nonmult=True):
        """Convert unit or dict of units to the root units.

        If any unit is non multiplicative and check_converter is True,
        then None is returned as the multiplicative factor.

        Parameters
        ----------
        input_units : UnitsContainer or dict
            units
        check_nonmult : bool
            if True, None will be returned as the
            multiplicative factor if a non-multiplicative
            units is found in the final Units. (Default value = True)

        Returns
        -------
        number, Unit
            multiplicative factor, base units

        """
        if not input_units:
            return 1, self.UnitsContainer()

        cache = self._cache.root_units
        try:
            return cache[input_units]
        except KeyError:
            pass

        accumulators = [1, defaultdict(int)]
        self._get_root_units_recurse(input_units, 1, accumulators)

        factor = accumulators[0]
        units = self.UnitsContainer(
            {k: v for k, v in accumulators[1].items() if v != 0}
        )

        # Check if any of the final units is non multiplicative and return None instead.
        if check_nonmult:
            if any(not self._units[unit].converter.is_multiplicative for unit in units):
                factor = None

        cache[input_units] = factor, units
        return factor, units

    def get_base_units(self, input_units, check_nonmult=True, system=None):
        """Convert unit or dict of units to the base units.

        If any unit is non multiplicative and check_converter is True,
        then None is returned as the multiplicative factor.

        Parameters
        ----------
        input_units : UnitsContainer or str
            units
        check_nonmult : bool
            If True, None will be returned as the multiplicative factor if
            non-multiplicative units are found in the final Units.
            (Default value = True)
        system :
             (Default value = None)

        Returns
        -------
        Number, pint.Unit
            multiplicative factor, base units

        """

        return self.get_root_units(input_units, check_nonmult)

    def _get_root_units_recurse(self, ref, exp, accumulators):
        for key in ref:
            exp2 = exp * ref[key]
            key = self.get_name(key)
            reg = self._units[key]
            if reg.is_base:
                accumulators[1][key] += exp2
            else:
                accumulators[0] *= reg._converter.scale ** exp2
                if reg.reference is not None:
                    self._get_root_units_recurse(reg.reference, exp2, accumulators)

    def get_compatible_units(self, input_units, group_or_system=None):
        """
        """
        input_units = to_units_container(input_units)

        equiv = self._get_compatible_units(input_units, group_or_system)

        return frozenset(self.Unit(eq) for eq in equiv)

    def _get_compatible_units(self, input_units, group_or_system):
        """
        """
        if not input_units:
            return frozenset()

        src_dim = self._get_dimensionality(input_units)
        return self._cache.dimensional_equivalents[src_dim]

    def is_compatible_with(self, obj1, obj2, *contexts, **ctx_kwargs):
        """ check if the other object is compatible

        Parameters
        ----------
        obj1, obj2
            The objects to check against each other. Treated as
            dimensionless if not a Quantity, Unit or str.
        *contexts : str or pint.Context
            Contexts to use in the transformation.
        **ctx_kwargs :
            Values for the Context/s

        Returns
        -------
        bool
        """
        if isinstance(obj1, (self.Quantity, self.Unit)):
            return obj1.is_compatible_with(obj2, *contexts, **ctx_kwargs)

        if isinstance(obj1, str):
            return self.parse_expression(obj1).is_compatible_with(
                obj2, *contexts, **ctx_kwargs
            )

        return not isinstance(obj2, (self.Quantity, self.Unit))

    def convert(self, value, src, dst, inplace=False):
        """Convert value from some source to destination units.

        Parameters
        ----------
        value :
            value
        src : pint.Quantity or str
            source units.
        dst : pint.Quantity or str
            destination units.
        inplace :
             (Default value = False)

        Returns
        -------
        type
            converted value

        """
        src = to_units_container(src, self)

        dst = to_units_container(dst, self)

        if src == dst:
            return value

        return self._convert(value, src, dst, inplace)

    def _convert(self, value, src, dst, inplace=False, check_dimensionality=True):
        """Convert value from some source to destination units.

        Parameters
        ----------
        value :
            value
        src : UnitsContainer
            source units.
        dst : UnitsContainer
            destination units.
        inplace :
             (Default value = False)
        check_dimensionality :
             (Default value = True)

        Returns
        -------
        type
            converted value

        """

        if check_dimensionality:

            src_dim = self._get_dimensionality(src)
            dst_dim = self._get_dimensionality(dst)

            # If the source and destination dimensionality are different,
            # then the conversion cannot be performed.
            if src_dim != dst_dim:
                raise DimensionalityError(src, dst, src_dim, dst_dim)

        # Here src and dst have only multiplicative units left. Thus we can
        # convert with a factor.
        factor, _ = self._get_root_units(src / dst)

        # factor is type float and if our magnitude is type Decimal then
        # must first convert to Decimal before we can '*' the values
        if isinstance(value, Decimal):
            factor = Decimal(str(factor))
        elif isinstance(value, Fraction):
            factor = Fraction(str(factor))

        if inplace:
            value *= factor
        else:
            value = value * factor

        return value

    def parse_unit_name(self, unit_name, case_sensitive=None):
        """Parse a unit to identify prefix, unit name and suffix
        by walking the list of prefix and suffix.
        In case of equivalent combinations (e.g. ('kilo', 'gram', '') and
        ('', 'kilogram', ''), prefer those with prefix.

        Parameters
        ----------
        unit_name :

        case_sensitive : bool or None
            Control if unit lookup is case sensitive. Defaults to None, which uses the
            registry's case_sensitive setting

        Returns
        -------
        tuple of tuples (str, str, str)
            all non-equivalent combinations of (prefix, unit name, suffix)
        """
        return self._dedup_candidates(
            self._parse_unit_name(unit_name, case_sensitive=case_sensitive)
        )

    def _parse_unit_name(self, unit_name, case_sensitive=None):
        """Helper of parse_unit_name.
        """
        case_sensitive = (
            self.case_sensitive if case_sensitive is None else case_sensitive
        )
        stw = unit_name.startswith
        edw = unit_name.endswith
        for suffix, prefix in itertools.product(self._suffixes, self._prefixes):
            if stw(prefix) and edw(suffix):
                name = unit_name[len(prefix) :]
                if suffix:
                    name = name[: -len(suffix)]
                    if len(name) == 1:
                        continue
                if case_sensitive:
                    if name in self._units:
                        yield (
                            self._prefixes[prefix].name,
                            self._units[name].name,
                            self._suffixes[suffix],
                        )
                else:
                    for real_name in self._units_casei.get(name.lower(), ()):
                        yield (
                            self._prefixes[prefix].name,
                            self._units[real_name].name,
                            self._suffixes[suffix],
                        )

    @staticmethod
    def _dedup_candidates(candidates):
        """Helper of parse_unit_name.

        Given an iterable of unit triplets (prefix, name, suffix), remove those with
        different names but equal value, preferring those with a prefix.

        e.g. ('kilo', 'gram', '') and ('', 'kilogram', '')
        """
        candidates = dict.fromkeys(candidates)  # ordered set
        for cp, cu, cs in list(candidates):
            assert isinstance(cp, str)
            assert isinstance(cu, str)
            if cs != "":
                raise NotImplementedError("non-empty suffix")
            if cp:
                candidates.pop(("", cp + cu, ""), None)
        return tuple(candidates)

    def parse_units(self, input_string, as_delta=None, case_sensitive=None):
        """Parse a units expression and returns a UnitContainer with
        the canonical names.

        The expression can only contain products, ratios and powers of units.

        Parameters
        ----------
        input_string : str
        as_delta : bool or None
            if the expression has multiple units, the parser will
            interpret non multiplicative units as their `delta_` counterparts. (Default value = None)
        case_sensitive : bool or None
            Control if unit parsing is case sensitive. Defaults to None, which uses the
            registry's setting.

        Returns
        -------

        """
        for p in self.preprocessors:
            input_string = p(input_string)
        units = self._parse_units(input_string, as_delta, case_sensitive)
        return self.Unit(units)

    def _parse_units(self, input_string, as_delta=True, case_sensitive=None):
        """Parse a units expression and returns a UnitContainer with
        the canonical names.
        """

        cache = self._cache.parse_unit
        # Issue #1097: it is possible, when a unit was defined while a different context
        # was active, that the unit is in self._cache.parse_unit but not in self._units.
        # If this is the case, force self._units to be repopulated.
        if as_delta and input_string in cache and input_string in self._units:
            return cache[input_string]

        if not input_string:
            return self.UnitsContainer()

        # Sanitize input_string with whitespaces.
        input_string = input_string.strip()

        units = ParserHelper.from_string(input_string, self.non_int_type)
        if units.scale != 1:
            raise ValueError("Unit expression cannot have a scaling factor.")

        ret = {}
        many = len(units) > 1
        for name in units:
            cname = self.get_name(name, case_sensitive=case_sensitive)
            value = units[name]
            if not cname:
                continue
            if as_delta and (many or (not many and value != 1)):
                definition = self._units[cname]
                if not definition.is_multiplicative:
                    cname = "delta_" + cname
            ret[cname] = value

        ret = self.UnitsContainer(ret)

        if as_delta:
            cache[input_string] = ret

        return ret

    def _eval_token(self, token, case_sensitive=None, use_decimal=False, **values):

        # TODO: remove this code when use_decimal is deprecated
        if use_decimal:
            raise DeprecationWarning(
                "`use_decimal` is deprecated, use `non_int_type` keyword argument when instantiating the registry.\n"
                ">>> from decimal import Decimal\n"
                ">>> ureg = UnitRegistry(non_int_type=Decimal)"
            )

        token_type = token[0]
        token_text = token[1]
        if token_type == NAME:
            if token_text == "dimensionless":
                return 1 * self.dimensionless
            elif token_text in values:
                return self.Quantity(values[token_text])
            else:
                return self.Quantity(
                    1,
                    self.UnitsContainer(
                        {self.get_name(token_text, case_sensitive=case_sensitive): 1}
                    ),
                )
        elif token_type == NUMBER:
            return ParserHelper.eval_token(token, non_int_type=self.non_int_type)
        else:
            raise Exception("unknown token type")

    def parse_pattern(
        self, input_string, pattern, case_sensitive=None, use_decimal=False, many=False
    ):
        """Parse a string with a given regex pattern and returns result.

        Parameters
        ----------
        input_string :

        pattern_string:
             The regex parse string
        case_sensitive :
             (Default value = None, which uses registry setting)
        use_decimal :
             (Default value = False)
        many :
             Match many results
             (Default value = False)


        Returns
        -------

        """

        if not input_string:
            return [] if many else None

        # Parse string
        pattern = pattern_to_regex(pattern)
        matched = re.finditer(pattern, input_string)

        # Extract result(s)
        results = []
        for match in matched:
            # Extract units from result
            match = match.groupdict()

            # Parse units
            units = []
            for unit, value in match.items():
                # Construct measure by multiplying value by unit
                units.append(
                    float(value)
                    * self.parse_expression(unit, case_sensitive, use_decimal)
                )

            # Add to results
            results.append(units)

            # Return first match only
            if not many:
                return results[0]

        return results

    def parse_expression(
        self, input_string, case_sensitive=None, use_decimal=False, **values
    ):
        """Parse a mathematical expression including units and return a quantity object.

        Numerical constants can be specified as keyword arguments and will take precedence
        over the names defined in the registry.

        Parameters
        ----------
        input_string :

        case_sensitive :
             (Default value = None, which uses registry setting)
        use_decimal :
             (Default value = False)
        **values :


        Returns
        -------

        """

        # TODO: remove this code when use_decimal is deprecated
        if use_decimal:
            raise DeprecationWarning(
                "`use_decimal` is deprecated, use `non_int_type` keyword argument when instantiating the registry.\n"
                ">>> from decimal import Decimal\n"
                ">>> ureg = UnitRegistry(non_int_type=Decimal)"
            )

        if not input_string:
            return self.Quantity(1)

        for p in self.preprocessors:
            input_string = p(input_string)
        input_string = string_preprocessor(input_string)
        gen = tokenizer(input_string)

        return build_eval_tree(gen).evaluate(
            lambda x: self._eval_token(x, case_sensitive=case_sensitive, **values)
        )

    __call__ = parse_expression


class NonMultiplicativeRegistry(BaseRegistry):
    """Handle of non multiplicative units (e.g. Temperature).

    Capabilities:
    - Register non-multiplicative units and their relations.
    - Convert between non-multiplicative units.

    Parameters
    ----------
    default_as_delta : bool
        If True, non-multiplicative units are interpreted as
        their *delta* counterparts in multiplications.
    autoconvert_offset_to_baseunit : bool
        If True, non-multiplicative units are
        converted to base units in multiplications.

    """

    def __init__(
        self, default_as_delta=True, autoconvert_offset_to_baseunit=False, **kwargs
    ):
        super().__init__(**kwargs)

        #: When performing a multiplication of units, interpret
        #: non-multiplicative units as their *delta* counterparts.
        self.default_as_delta = default_as_delta

        # Determines if quantities with offset units are converted to their
        # base units on multiplication and division.
        self.autoconvert_offset_to_baseunit = autoconvert_offset_to_baseunit

    def _parse_units(self, input_string, as_delta=None, case_sensitive=None):
        """
        """
        if as_delta is None:
            as_delta = self.default_as_delta

        return super()._parse_units(input_string, as_delta, case_sensitive)

    def _define(self, definition):
        """Add unit to the registry.

        In addition to what is done by the BaseRegistry,
        registers also non-multiplicative units.

        Parameters
        ----------
        definition : str or Definition
            A dimension, unit or prefix definition.

        Returns
        -------
        Definition, dict, dict
            Definition instance, case sensitive unit dict, case insensitive unit dict.

        """

        definition, d, di = super()._define(definition)

        # define additional units for units with an offset
        if getattr(definition.converter, "offset", 0) != 0:
            self._define_adder(definition, d, di)

        return definition, d, di

    def _is_multiplicative(self, u):
        if u in self._units:
            return self._units[u].is_multiplicative

        # If the unit is not in the registry might be because it is not
        # registered with its prefixed version.
        # TODO: Might be better to register them.
        names = self.parse_unit_name(u)
        assert len(names) == 1
        _, base_name, _ = names[0]
        try:
            return self._units[base_name].is_multiplicative
        except KeyError:
            raise UndefinedUnitError(u)

    def _validate_and_extract(self, units):
        # u is for unit, e is for exponent
        nonmult_units = [
            (u, e) for u, e in units.items() if not self._is_multiplicative(u)
        ]

        # Let's validate source offset units
        if len(nonmult_units) > 1:
            # More than one src offset unit is not allowed
            raise ValueError("more than one offset unit.")

        elif len(nonmult_units) == 1:
            # A single src offset unit is present. Extract it
            # But check that:
            # - the exponent is 1
            # - is not used in multiplicative context
            nonmult_unit, exponent = nonmult_units.pop()

            if exponent != 1:
                raise ValueError("offset units in higher order.")

            if len(units) > 1 and not self.autoconvert_offset_to_baseunit:
                raise ValueError("offset unit used in multiplicative context.")

            return nonmult_unit

        return None

    def _add_ref_of_log_unit(self, offset_unit, all_units):

        slct_unit = self._units[offset_unit]
        if isinstance(slct_unit.converter, LogarithmicConverter):
            # Extract reference unit
            slct_ref = slct_unit.reference
            # If reference unit is not dimensionless
            if slct_ref != UnitsContainer():
                # Extract reference unit
                (u, e) = [(u, e) for u, e in slct_ref.items()].pop()
                # Add it back to the unit list
                return all_units.add(u, e)
        # Otherwise, return the units unmodified
        return all_units

    def _convert(self, value, src, dst, inplace=False):
        """Convert value from some source to destination units.

        In addition to what is done by the BaseRegistry,
        converts between non-multiplicative units.

        Parameters
        ----------
        value :
            value
        src : UnitsContainer
            source units.
        dst : UnitsContainer
            destination units.
        inplace :
             (Default value = False)

        Returns
        -------
        type
            converted value

        """

        # Conversion needs to consider if non-multiplicative (AKA offset
        # units) are involved. Conversion is only possible if src and dst
        # have at most one offset unit per dimension. Other rules are applied
        # by validate and extract.
        try:
            src_offset_unit = self._validate_and_extract(src)
        except ValueError as ex:
            raise DimensionalityError(src, dst, extra_msg=f" - In source units, {ex}")

        try:
            dst_offset_unit = self._validate_and_extract(dst)
        except ValueError as ex:
            raise DimensionalityError(
                src, dst, extra_msg=f" - In destination units, {ex}"
            )

        if not (src_offset_unit or dst_offset_unit):
            return super()._convert(value, src, dst, inplace)

        src_dim = self._get_dimensionality(src)
        dst_dim = self._get_dimensionality(dst)

        # If the source and destination dimensionality are different,
        # then the conversion cannot be performed.
        if src_dim != dst_dim:
            raise DimensionalityError(src, dst, src_dim, dst_dim)

        # clean src from offset units by converting to reference
        if src_offset_unit:
            value = self._units[src_offset_unit].converter.to_reference(value, inplace)
            src = src.remove([src_offset_unit])
            # Add reference unit for multiplicative section
            src = self._add_ref_of_log_unit(src_offset_unit, src)

        # clean dst units from offset units
        if dst_offset_unit:
            dst = dst.remove([dst_offset_unit])
            # Add reference unit for multiplicative section
            dst = self._add_ref_of_log_unit(dst_offset_unit, dst)

        # Convert non multiplicative units to the dst.
        value = super()._convert(value, src, dst, inplace, False)

        # Finally convert to offset units specified in destination
        if dst_offset_unit:
            value = self._units[dst_offset_unit].converter.from_reference(
                value, inplace
            )

        return value


class ContextRegistry(BaseRegistry):
    """Handle of Contexts.

    Conversion between units with different dimenstions according
    to previously established relations (contexts).
    (e.g. in the spectroscopy, conversion between frequency and energy is possible)

    Capabilities:

    - Register contexts.
    - Enable and disable contexts.
    - Parse @context directive.
    """

    def __init__(self, **kwargs):
        # Map context name (string) or abbreviation to context.
        self._contexts = {}
        # Stores active contexts.
        self._active_ctx = ContextChain()
        # Map context chain to cache
        self._caches = {}
        # Map context chain to units override
        self._context_units = {}

        super().__init__(**kwargs)

        # Allow contexts to add override layers to the units
        self._units = ChainMap(self._units)

    def _register_parsers(self):
        super()._register_parsers()
        self._register_parser("@context", self._parse_context)

    def _parse_context(self, ifile):
        try:
            self.add_context(
                Context.from_lines(
                    ifile.block_iter(),
                    self.get_dimensionality,
                    non_int_type=self.non_int_type,
                )
            )
        except KeyError as e:
            raise DefinitionSyntaxError(f"unknown dimension {e} in context")

    def add_context(self, context: Context) -> None:
        """Add a context object to the registry.

        The context will be accessible by its name and aliases.

        Notice that this method will NOT enable the context;
        see :meth:`enable_contexts`.
        """
        if not context.name:
            raise ValueError("Can't add unnamed context to registry")
        if context.name in self._contexts:
            logger.warning(
                "The name %s was already registered for another context.", context.name
            )
        self._contexts[context.name] = context
        for alias in context.aliases:
            if alias in self._contexts:
                logger.warning(
                    "The name %s was already registered for another context",
                    context.name,
                )
            self._contexts[alias] = context

    def remove_context(self, name_or_alias: str) -> Context:
        """Remove a context from the registry and return it.

        Notice that this methods will not disable the context;
        see :meth:`disable_contexts`.
        """
        context = self._contexts[name_or_alias]

        del self._contexts[context.name]
        for alias in context.aliases:
            del self._contexts[alias]

        return context

    def _build_cache(self) -> None:
        super()._build_cache()
        self._caches[()] = self._cache

    def _switch_context_cache_and_units(self) -> None:
        """If any of the active contexts redefine units, create variant self._cache
        and self._units specific to the combination of active contexts.
        The next time this method is invoked with the same combination of contexts,
        reuse the same variant self._cache and self._units as in the previous time.
        """
        del self._units.maps[:-1]
        units_overlay = any(ctx.redefinitions for ctx in self._active_ctx.contexts)
        if not units_overlay:
            # Use the default _cache and _units
            self._cache = self._caches[()]
            return

        key = self._active_ctx.hashable()
        try:
            self._cache = self._caches[key]
            self._units.maps.insert(0, self._context_units[key])
        except KeyError:
            pass

        # First time using this specific combination of contexts and it contains
        # unit redefinitions
        base_cache = self._caches[()]
        self._caches[key] = self._cache = ContextCacheOverlay(base_cache)

        self._context_units[key] = units_overlay = {}
        self._units.maps.insert(0, units_overlay)

        on_redefinition_backup = self._on_redefinition
        self._on_redefinition = "ignore"
        try:
            for ctx in reversed(self._active_ctx.contexts):
                for definition in ctx.redefinitions:
                    self._redefine(definition)
        finally:
            self._on_redefinition = on_redefinition_backup

    def _redefine(self, definition: UnitDefinition) -> None:
        """Redefine a unit from a context
        """
        # Find original definition in the UnitRegistry
        candidates = self.parse_unit_name(definition.name)
        if not candidates:
            raise UndefinedUnitError(definition.name)
        candidates_no_prefix = [c for c in candidates if not c[0]]
        if not candidates_no_prefix:
            raise ValueError(f"Can't redefine a unit with a prefix: {definition.name}")
        assert len(candidates_no_prefix) == 1
        _, name, _ = candidates_no_prefix[0]
        try:
            basedef = self._units[name]
        except KeyError:
            raise UndefinedUnitError(name)

        # Rebuild definition as a variant of the base
        if basedef.is_base:
            raise ValueError("Can't redefine a base unit to a derived one")

        dims_old = self._get_dimensionality(basedef.reference)
        dims_new = self._get_dimensionality(definition.reference)
        if dims_old != dims_new:
            raise ValueError(
                f"Can't change dimensionality of {basedef.name} "
                f"from {dims_old} to {dims_new} in a context"
            )

        # Do not modify in place the original definition, as (1) the context may
        # be shared by other registries, and (2) it would alter the cache key
        definition = UnitDefinition(
            name=basedef.name,
            symbol=basedef.symbol,
            aliases=basedef.aliases,
            is_base=False,
            reference=definition.reference,
            converter=definition.converter,
        )

        # Write into the context-specific self._units.maps[0] and self._cache.root_units
        self.define(definition)

    def enable_contexts(self, *names_or_contexts, **kwargs) -> None:
        """Enable contexts provided by name or by object.

        Parameters
        ----------
        *names_or_contexts :
            one or more contexts or context names/aliases
        **kwargs :
            keyword arguments for the context(s)

        Examples
        --------
        See :meth:`context`
        """

        # If present, copy the defaults from the containing contexts
        if self._active_ctx.defaults:
            kwargs = dict(self._active_ctx.defaults, **kwargs)

        # For each name, we first find the corresponding context
        ctxs = [
            self._contexts[name] if isinstance(name, str) else name
            for name in names_or_contexts
        ]

        # Check if the contexts have been checked first, if not we make sure
        # that dimensions are expressed in terms of base dimensions.
        for ctx in ctxs:
            if ctx.checked:
                continue
            funcs_copy = dict(ctx.funcs)
            for (src, dst), func in funcs_copy.items():
                src_ = self._get_dimensionality(src)
                dst_ = self._get_dimensionality(dst)
                if src != src_ or dst != dst_:
                    ctx.remove_transformation(src, dst)
                    ctx.add_transformation(src_, dst_, func)
            ctx.checked = True

        # and create a new one with the new defaults.
        ctxs = tuple(Context.from_context(ctx, **kwargs) for ctx in ctxs)

        # Finally we add them to the active context.
        self._active_ctx.insert_contexts(*ctxs)
        self._switch_context_cache_and_units()

    def disable_contexts(self, n: int = None) -> None:
        """Disable the last n enabled contexts.

        Parameters
        ----------
        n : int
            Number of contexts to disable. Default: disable all contexts.
        """
        self._active_ctx.remove_contexts(n)
        self._switch_context_cache_and_units()

    @contextmanager
    def context(self, *names, **kwargs):
        """Used as a context manager, this function enables to activate a context
        which is removed after usage.

        Parameters
        ----------
        *names :
            name(s) of the context(s).
        **kwargs :
            keyword arguments for the contexts.

        Examples
        --------
        Context can be called by their name:

          >>> import pint
          >>> ureg = pint.UnitRegistry()
          >>> ureg.add_context(pint.Context('one'))
          >>> ureg.add_context(pint.Context('two'))
          >>> with ureg.context('one'):
          ...     pass

        If a context has an argument, you can specify its value as a keyword argument:

          >>> with ureg.context('one', n=1):
          ...     pass

        Multiple contexts can be entered in single call:

          >>> with ureg.context('one', 'two', n=1):
          ...     pass

        Or nested allowing you to give different values to the same keyword argument:

          >>> with ureg.context('one', n=1):
          ...     with ureg.context('two', n=2):
          ...         pass

        A nested context inherits the defaults from the containing context:

          >>> with ureg.context('one', n=1):
          ...     # Here n takes the value of the outer context
          ...     with ureg.context('two'):
          ...         pass
        """
        # Enable the contexts.
        self.enable_contexts(*names, **kwargs)

        try:
            # After adding the context and rebuilding the graph, the registry
            # is ready to use.
            yield self
        finally:
            # Upon leaving the with statement,
            # the added contexts are removed from the active one.
            self.disable_contexts(len(names))

    def with_context(self, name, **kwargs):
        """Decorator to wrap a function call in a Pint context.

        Use it to ensure that a certain context is active when
        calling a function::

        Parameters
        ----------
        name :
            name of the context.
        **kwargs :
            keyword arguments for the context


        Returns
        -------
        callable
            the wrapped function.

        Example
        -------
          >>> @ureg.with_context('sp')
          ... def my_cool_fun(wavelength):
          ...     print('This wavelength is equivalent to: %s', wavelength.to('terahertz'))
        """

        def decorator(func):
            assigned = tuple(
                attr for attr in functools.WRAPPER_ASSIGNMENTS if hasattr(func, attr)
            )
            updated = tuple(
                attr for attr in functools.WRAPPER_UPDATES if hasattr(func, attr)
            )

            @functools.wraps(func, assigned=assigned, updated=updated)
            def wrapper(*values, **wrapper_kwargs):
                with self.context(name, **kwargs):
                    return func(*values, **wrapper_kwargs)

            return wrapper

        return decorator

    def _convert(self, value, src, dst, inplace=False):
        """Convert value from some source to destination units.

        In addition to what is done by the BaseRegistry,
        converts between units with different dimensions by following
        transformation rules defined in the context.

        Parameters
        ----------
        value :
            value
        src : UnitsContainer
            source units.
        dst : UnitsContainer
            destination units.
        inplace :
             (Default value = False)

        Returns
        -------
        callable
            converted value
        """
        # If there is an active context, we look for a path connecting source and
        # destination dimensionality. If it exists, we transform the source value
        # by applying sequentially each transformation of the path.
        if self._active_ctx:

            src_dim = self._get_dimensionality(src)
            dst_dim = self._get_dimensionality(dst)

            path = find_shortest_path(self._active_ctx.graph, src_dim, dst_dim)
            if path:
                src = self.Quantity(value, src)
                for a, b in zip(path[:-1], path[1:]):
                    src = self._active_ctx.transform(a, b, self, src)

                value, src = src._magnitude, src._units

        return super()._convert(value, src, dst, inplace)

    def _get_compatible_units(self, input_units, group_or_system):
        src_dim = self._get_dimensionality(input_units)

        ret = super()._get_compatible_units(input_units, group_or_system)

        if self._active_ctx:
            ret = ret.copy()  # Do not alter self._cache
            nodes = find_connected_nodes(self._active_ctx.graph, src_dim)
            if nodes:
                for node in nodes:
                    ret |= self._cache.dimensional_equivalents[node]

        return ret


class SystemRegistry(BaseRegistry):
    """Handle of Systems and Groups.

    Conversion between units with different dimenstions according
    to previously established relations (contexts).
    (e.g. in the spectroscopy, conversion between frequency and energy is possible)

    Capabilities:

    - Register systems and groups.
    - List systems
    - Get or get the default system.
    - Parse @system and @group directive.
    """

    def __init__(self, system=None, **kwargs):
        super().__init__(**kwargs)

        #: Map system name to system.
        #: :type: dict[ str | System]
        self._systems = {}

        #: Maps dimensionality (UnitsContainer) to Dimensionality (UnitsContainer)
        self._base_units_cache = dict()

        #: Map group name to group.
        #: :type: dict[ str | Group]
        self._groups = {}
        self._groups["root"] = self.Group("root")
        self._default_system = system

    def _init_dynamic_classes(self):
        super()._init_dynamic_classes()
        self.Group = systems.build_group_class(self)
        self.System = systems.build_system_class(self)

    def _after_init(self):
        """Invoked at the end of ``__init__``.

        - Create default group and add all orphan units to it
        - Set default system
        """
        super()._after_init()

        #: Copy units not defined in any group to the default group
        if "group" in self._defaults:
            grp = self.get_group(self._defaults["group"], True)
            group_units = frozenset(
                [
                    member
                    for group in self._groups.values()
                    if group.name != "root"
                    for member in group.members
                ]
            )
            all_units = self.get_group("root", False).members
            grp.add_units(*(all_units - group_units))

        #: System name to be used by default.
        self._default_system = self._default_system or self._defaults.get(
            "system", None
        )

    def _register_parsers(self):
        super()._register_parsers()
        self._register_parser("@group", self._parse_group)
        self._register_parser("@system", self._parse_system)

    def _parse_group(self, ifile):
        self.Group.from_lines(ifile.block_iter(), self.define, self.non_int_type)

    def _parse_system(self, ifile):
        self.System.from_lines(
            ifile.block_iter(), self.get_root_units, self.non_int_type
        )

    def get_group(self, name, create_if_needed=True):
        """Return a Group.

        Parameters
        ----------
        name : str
            Name of the group to be
        create_if_needed : bool
            If True, create a group if not found. If False, raise an Exception.
            (Default value = True)

        Returns
        -------
        type
            Group
        """
        if name in self._groups:
            return self._groups[name]

        if not create_if_needed:
            raise ValueError("Unkown group %s" % name)

        return self.Group(name)

    @property
    def sys(self):
        return systems.Lister(self._systems)

    @property
    def default_system(self):
        return self._default_system

    @default_system.setter
    def default_system(self, name):
        if name:
            if name not in self._systems:
                raise ValueError("Unknown system %s" % name)

            self._base_units_cache = {}

        self._default_system = name

    def get_system(self, name, create_if_needed=True):
        """Return a Group.

        Parameters
        ----------
        name : str
            Name of the group to be
        create_if_needed : bool
            If True, create a group if not found. If False, raise an Exception.
            (Default value = True)

        Returns
        -------
        type
            System

        """
        if name in self._systems:
            return self._systems[name]

        if not create_if_needed:
            raise ValueError("Unkown system %s" % name)

        return self.System(name)

    def _define(self, definition):

        # In addition to the what is done by the BaseRegistry,
        # this adds all units to the `root` group.

        definition, d, di = super()._define(definition)

        if isinstance(definition, UnitDefinition):
            # We add all units to the root group
            self.get_group("root").add_units(definition.name)

        return definition, d, di

    def get_base_units(self, input_units, check_nonmult=True, system=None):
        """Convert unit or dict of units to the base units.

        If any unit is non multiplicative and check_converter is True,
        then None is returned as the multiplicative factor.

        Unlike BaseRegistry, in this registry root_units might be different
        from base_units

        Parameters
        ----------
        input_units : UnitsContainer or str
            units
        check_nonmult : bool
            if True, None will be returned as the
            multiplicative factor if a non-multiplicative
            units is found in the final Units. (Default value = True)
        system :
             (Default value = None)

        Returns
        -------
        type
            multiplicative factor, base units

        """

        input_units = to_units_container(input_units)

        f, units = self._get_base_units(input_units, check_nonmult, system)

        return f, self.Unit(units)

    def _get_base_units(self, input_units, check_nonmult=True, system=None):

        if system is None:
            system = self._default_system

        # The cache is only done for check_nonmult=True and the current system.
        if (
            check_nonmult
            and system == self._default_system
            and input_units in self._base_units_cache
        ):
            return self._base_units_cache[input_units]

        factor, units = self.get_root_units(input_units, check_nonmult)

        if not system:
            return factor, units

        # This will not be necessary after integration with the registry
        # as it has a UnitsContainer intermediate
        units = to_units_container(units, self)

        destination_units = self.UnitsContainer()

        bu = self.get_system(system, False).base_units

        for unit, value in units.items():
            if unit in bu:
                new_unit = bu[unit]
                new_unit = to_units_container(new_unit, self)
                destination_units *= new_unit ** value
            else:
                destination_units *= self.UnitsContainer({unit: value})

        base_factor = self.convert(factor, units, destination_units)

        if check_nonmult:
            self._base_units_cache[input_units] = base_factor, destination_units

        return base_factor, destination_units

    def _get_compatible_units(self, input_units, group_or_system):

        if group_or_system is None:
            group_or_system = self._default_system

        ret = super()._get_compatible_units(input_units, group_or_system)

        if group_or_system:
            if group_or_system in self._systems:
                members = self._systems[group_or_system].members
            elif group_or_system in self._groups:
                members = self._groups[group_or_system].members
            else:
                raise ValueError(
                    "Unknown Group o System with name '%s'" % group_or_system
                )
            return frozenset(ret & members)

        return ret


class UnitRegistry(SystemRegistry, ContextRegistry, NonMultiplicativeRegistry):
    """The unit registry stores the definitions and relationships between units.

    Parameters
    ----------
    filename :
        path of the units definition file to load or line-iterable object.
        Empty to load the default definition file.
        None to leave the UnitRegistry empty.
    force_ndarray : bool
        convert any input, scalar or not to a numpy.ndarray.
    force_ndarray_like : bool
        convert all inputs other than duck arrays to a numpy.ndarray.
    default_as_delta :
        In the context of a multiplication of units, interpret
        non-multiplicative units as their *delta* counterparts.
    autoconvert_offset_to_baseunit :
        If True converts offset units in quantites are
        converted to their base units in multiplicative
        context. If False no conversion happens.
    on_redefinition : str
        action to take in case a unit is redefined.
        'warn', 'raise', 'ignore'
    auto_reduce_dimensions :
        If True, reduce dimensionality on appropriate operations.
    preprocessors :
        list of callables which are iteratively ran on any input expression
        or unit string
    fmt_locale :
        locale identifier string, used in `format_babel`. Default to None
    case_sensitive : bool, optional
        Control default case sensitivity of unit parsing. (Default: True)
    """

    def __init__(
        self,
        filename="",
        force_ndarray=False,
        force_ndarray_like=False,
        default_as_delta=True,
        autoconvert_offset_to_baseunit=False,
        on_redefinition="warn",
        system=None,
        auto_reduce_dimensions=False,
        preprocessors=None,
        fmt_locale=None,
        non_int_type=float,
        case_sensitive=True,
    ):

        super().__init__(
            filename=filename,
            force_ndarray=force_ndarray,
            force_ndarray_like=force_ndarray_like,
            on_redefinition=on_redefinition,
            default_as_delta=default_as_delta,
            autoconvert_offset_to_baseunit=autoconvert_offset_to_baseunit,
            system=system,
            auto_reduce_dimensions=auto_reduce_dimensions,
            preprocessors=preprocessors,
            fmt_locale=fmt_locale,
            non_int_type=non_int_type,
            case_sensitive=case_sensitive,
        )

    def pi_theorem(self, quantities):
        """Builds dimensionless quantities using the Buckingham π theorem

        Parameters
        ----------
        quantities : dict
            mapping between variable name and units

        Returns
        -------
        list
            a list of dimensionless quantities expressed as dicts

        """
        return pi_theorem(quantities, self)

    def setup_matplotlib(self, enable=True):
        """Set up handlers for matplotlib's unit support.

        Parameters
        ----------
        enable : bool
            whether support should be enabled or disabled (Default value = True)

        """
        # Delays importing matplotlib until it's actually requested
        from .matplotlib import setup_matplotlib_handlers

        setup_matplotlib_handlers(self, enable)

    wraps = registry_helpers.wraps

    check = registry_helpers.check


class LazyRegistry:
    def __init__(self, args=None, kwargs=None):
        self.__dict__["params"] = args or (), kwargs or {}

    def __init(self):
        args, kwargs = self.__dict__["params"]
        kwargs["on_redefinition"] = "raise"
        self.__class__ = UnitRegistry
        self.__init__(*args, **kwargs)
        self._after_init()

    def __getattr__(self, item):
        if item == "_on_redefinition":
            return "raise"
        self.__init()
        return getattr(self, item)

    def __setattr__(self, key, value):
        if key == "__class__":
            super().__setattr__(key, value)
        else:
            self.__init()
            setattr(self, key, value)

    def __getitem__(self, item):
        self.__init()
        return self[item]

    def __call__(self, *args, **kwargs):
        self.__init()
        return self(*args, **kwargs)
