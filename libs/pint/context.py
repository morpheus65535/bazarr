"""
    pint.context
    ~~~~~~~~~~~~

    Functions and classes related to context definitions and application.

    :copyright: 2016 by Pint Authors, see AUTHORS for more details..
    :license: BSD, see LICENSE for more details.
"""

import re
import weakref
from collections import ChainMap, defaultdict

from .definitions import Definition, UnitDefinition
from .errors import DefinitionSyntaxError
from .util import ParserHelper, SourceIterator, to_units_container

#: Regex to match the header parts of a context.
_header_re = re.compile(
    r"@context\s*(?P<defaults>\(.*\))?\s+(?P<name>\w+)\s*(=(?P<aliases>.*))*"
)

#: Regex to match variable names in an equation.
_varname_re = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _expression_to_function(eq):
    def func(ureg, value, **kwargs):
        return ureg.parse_expression(eq, value=value, **kwargs)

    return func


class Context:
    """A specialized container that defines transformation functions from one
    dimension to another. Each Dimension are specified using a UnitsContainer.
    Simple transformation are given with a function taking a single parameter.


    Conversion functions may take optional keyword arguments and the context
    can have default values for these arguments.


    Additionally, a context may host redefinitions:


    A redefinition must be performed among units that already exist in the registry. It
    cannot change the dimensionality of a unit. The symbol and aliases are automatically
    inherited from the registry.

    Parameters
    ----------
    name : str or None, optional
        Name of the context (must be unique within the registry).
        Use None for anonymous Context. (Default value = None).
    aliases : iterable of str
        Other names for the context.
    defaults : None or dict
        Maps variable names to values.

    Example
    -------

    >>> from pint.util import UnitsContainer
    >>> from pint import Context, UnitRegistry
    >>> ureg = UnitRegistry()
    >>> timedim = UnitsContainer({'[time]': 1})
    >>> spacedim = UnitsContainer({'[length]': 1})
    >>> def time_to_len(ureg, time):
    ...     'Time to length converter'
    ...     return 3. * time
    >>> c = Context()
    >>> c.add_transformation(timedim, spacedim, time_to_len)
    >>> c.transform(timedim, spacedim, ureg, 2)
    6.0
    >>> def time_to_len_indexed(ureg, time, n=1):
    ...     'Time to length converter, n is the index of refraction of the material'
    ...     return 3. * time / n
    >>> c = Context(defaults={'n':3})
    >>> c.add_transformation(timedim, spacedim, time_to_len_indexed)
    >>> c.transform(timedim, spacedim, ureg, 2)
    2.0
    >>> c.redefine("pound = 0.5 kg")
    """

    def __init__(self, name=None, aliases=(), defaults=None):

        self.name = name
        self.aliases = aliases

        #: Maps (src, dst) -> transformation function
        self.funcs = {}

        #: Maps defaults variable names to values
        self.defaults = defaults or {}

        # Store Definition objects that are context-specific
        self.redefinitions = []

        # Flag set to True by the Registry the first time the context is enabled
        self.checked = False

        #: Maps (src, dst) -> self
        #: Used as a convenience dictionary to be composed by ContextChain
        self.relation_to_context = weakref.WeakValueDictionary()

    @classmethod
    def from_context(cls, context, **defaults):
        """Creates a new context that shares the funcs dictionary with the
        original context. The default values are copied from the original
        context and updated with the new defaults.

        If defaults is empty, return the same context.

        Parameters
        ----------
        context : pint.Context
            Original context.
        **defaults


        Returns
        -------
        pint.Context
        """
        if defaults:
            newdef = dict(context.defaults, **defaults)
            c = cls(context.name, context.aliases, newdef)
            c.funcs = context.funcs
            c.redefinitions = context.redefinitions
            for edge in context.funcs:
                c.relation_to_context[edge] = c
            return c
        return context

    @classmethod
    def from_lines(cls, lines, to_base_func=None, non_int_type=float):
        lines = SourceIterator(lines)

        lineno, header = next(lines)
        try:
            r = _header_re.search(header)
            name = r.groupdict()["name"].strip()
            aliases = r.groupdict()["aliases"]
            if aliases:
                aliases = tuple(a.strip() for a in r.groupdict()["aliases"].split("="))
            else:
                aliases = ()
            defaults = r.groupdict()["defaults"]
        except Exception as exc:
            raise DefinitionSyntaxError(
                "Could not parse the Context header '%s'" % header, lineno=lineno
            ) from exc

        if defaults:

            def to_num(val):
                val = complex(val)
                if not val.imag:
                    return val.real
                return val

            txt = defaults
            try:
                defaults = (part.split("=") for part in defaults.strip("()").split(","))
                defaults = {str(k).strip(): to_num(v) for k, v in defaults}
            except (ValueError, TypeError) as exc:
                raise DefinitionSyntaxError(
                    f"Could not parse Context definition defaults: '{txt}'",
                    lineno=lineno,
                ) from exc

            ctx = cls(name, aliases, defaults)
        else:
            ctx = cls(name, aliases)

        names = set()
        for lineno, line in lines:
            if "=" in line:
                ctx.redefine(line)
                continue

            try:
                rel, eq = line.split(":")
                names.update(_varname_re.findall(eq))

                func = _expression_to_function(eq)

                if "<->" in rel:
                    src, dst = (
                        ParserHelper.from_string(s, non_int_type)
                        for s in rel.split("<->")
                    )
                    if to_base_func:
                        src = to_base_func(src)
                        dst = to_base_func(dst)
                    ctx.add_transformation(src, dst, func)
                    ctx.add_transformation(dst, src, func)
                elif "->" in rel:
                    src, dst = (
                        ParserHelper.from_string(s, non_int_type)
                        for s in rel.split("->")
                    )
                    if to_base_func:
                        src = to_base_func(src)
                        dst = to_base_func(dst)
                    ctx.add_transformation(src, dst, func)
                else:
                    raise Exception
            except Exception as exc:
                raise DefinitionSyntaxError(
                    "Could not parse Context %s relation '%s'" % (name, line),
                    lineno=lineno,
                ) from exc

        if defaults:
            missing_pars = defaults.keys() - set(names)
            if missing_pars:
                raise DefinitionSyntaxError(
                    f"Context parameters {missing_pars} not found in any equation"
                )

        return ctx

    def add_transformation(self, src, dst, func):
        """Add a transformation function to the context.
        """

        _key = self.__keytransform__(src, dst)
        self.funcs[_key] = func
        self.relation_to_context[_key] = self

    def remove_transformation(self, src, dst):
        """Add a transformation function to the context.
        """

        _key = self.__keytransform__(src, dst)
        del self.funcs[_key]
        del self.relation_to_context[_key]

    @staticmethod
    def __keytransform__(src, dst):
        return to_units_container(src), to_units_container(dst)

    def transform(self, src, dst, registry, value):
        """Transform a value.
        """

        _key = self.__keytransform__(src, dst)
        return self.funcs[_key](registry, value, **self.defaults)

    def redefine(self, definition: str) -> None:
        """Override the definition of a unit in the registry.

        Parameters
        ----------
        definition : str
            <unit> = <new definition>``, e.g. ``pound = 0.5 kg``
        """

        for line in definition.splitlines():
            d = Definition.from_string(line)
            if not isinstance(d, UnitDefinition):
                raise DefinitionSyntaxError(
                    "Expected <unit> = <converter>; got %s" % line.strip()
                )
            if d.symbol != d.name or d.aliases:
                raise DefinitionSyntaxError(
                    "Can't change a unit's symbol or aliases within a context"
                )
            if d.is_base:
                raise DefinitionSyntaxError("Can't define base units within a context")
            self.redefinitions.append(d)

    def hashable(self):
        """Generate a unique hashable and comparable representation of self, which can
        be used as a key in a dict. This class cannot define ``__hash__`` because it is
        mutable, and the Python interpreter does cache the output of ``__hash__``.

        Returns
        -------
        tuple
        """
        return (
            self.name,
            tuple(self.aliases),
            frozenset((k, id(v)) for k, v in self.funcs.items()),
            frozenset(self.defaults.items()),
            tuple(self.redefinitions),
        )


class ContextChain(ChainMap):
    """A specialized ChainMap for contexts that simplifies finding rules
    to transform from one dimension to another.
    """

    def __init__(self):
        super().__init__()
        self.contexts = []
        self.maps.clear()  # Remove default empty map
        self._graph = None

    def insert_contexts(self, *contexts):
        """Insert one or more contexts in reversed order the chained map.
        (A rule in last context will take precedence)

        To facilitate the identification of the context with the matching rule,
        the *relation_to_context* dictionary of the context is used.
        """

        self.contexts = list(reversed(contexts)) + self.contexts
        self.maps = [ctx.relation_to_context for ctx in reversed(contexts)] + self.maps
        self._graph = None

    def remove_contexts(self, n: int = None):
        """Remove the last n inserted contexts from the chain.

        Parameters
        ----------
        n: int
            (Default value = None)
        """

        del self.contexts[:n]
        del self.maps[:n]
        self._graph = None

    @property
    def defaults(self):
        for ctx in self.values():
            return ctx.defaults
        return {}

    @property
    def graph(self):
        """The graph relating"""
        if self._graph is None:
            self._graph = defaultdict(set)
            for fr_, to_ in self:
                self._graph[fr_].add(to_)
        return self._graph

    def transform(self, src, dst, registry, value):
        """Transform the value, finding the rule in the chained context.
        (A rule in last context will take precedence)
        """
        return self[(src, dst)].transform(src, dst, registry, value)

    def hashable(self):
        """Generate a unique hashable and comparable representation of self, which can
        be used as a key in a dict. This class cannot define ``__hash__`` because it is
        mutable, and the Python interpreter does cache the output of ``__hash__``.
        """
        return tuple(ctx.hashable() for ctx in self.contexts)
