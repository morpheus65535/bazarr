"""
    pint.systems
    ~~~~~~~~~~~~

    Functions and classes related to system definitions and conversions.

    :copyright: 2016 by Pint Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import re

from .babel_names import _babel_systems
from .compat import babel_parse
from .definitions import Definition, UnitDefinition
from .errors import DefinitionSyntaxError, RedefinitionError
from .util import (
    SharedRegistryObject,
    SourceIterator,
    getattr_maybe_raise,
    logger,
    to_units_container,
)


class Group(SharedRegistryObject):
    """A group is a set of units.

    Units can be added directly or by including other groups.

    Members are computed dynamically, that is if a unit is added to a group X
    all groups that include X are affected.

    The group belongs to one Registry.

    It can be specified in the definition file as::

        @group <name> [using <group 1>, ..., <group N>]
            <definition 1>
            ...
            <definition N>
        @end
    """

    #: Regex to match the header parts of a definition.
    _header_re = re.compile(r"@group\s+(?P<name>\w+)\s*(using\s(?P<used_groups>.*))*")

    def __init__(self, name):
        """
        :param name: Name of the group. If not given, a root Group will be created.
        :type name: str
        :param groups: dictionary like object groups and system.
                        The newly created group will be added after creation.
        :type groups: dict[str | Group]
        """

        # The name of the group.
        #: type: str
        self.name = name

        #: Names of the units in this group.
        #: :type: set[str]
        self._unit_names = set()

        #: Names of the groups in this group.
        #: :type: set[str]
        self._used_groups = set()

        #: Names of the groups in which this group is contained.
        #: :type: set[str]
        self._used_by = set()

        # Add this group to the group dictionary
        self._REGISTRY._groups[self.name] = self

        if name != "root":
            # All groups are added to root group
            self._REGISTRY._groups["root"].add_groups(name)

        #: A cache of the included units.
        #: None indicates that the cache has been invalidated.
        #: :type: frozenset[str] | None
        self._computed_members = None

    @property
    def members(self):
        """Names of the units that are members of the group.

        Calculated to include to all units in all included _used_groups.

        """
        if self._computed_members is None:
            self._computed_members = set(self._unit_names)

            for _, group in self.iter_used_groups():
                self._computed_members |= group.members

            self._computed_members = frozenset(self._computed_members)

        return self._computed_members

    def invalidate_members(self):
        """Invalidate computed members in this Group and all parent nodes."""
        self._computed_members = None
        d = self._REGISTRY._groups
        for name in self._used_by:
            d[name].invalidate_members()

    def iter_used_groups(self):
        pending = set(self._used_groups)
        d = self._REGISTRY._groups
        while pending:
            name = pending.pop()
            group = d[name]
            pending |= group._used_groups
            yield name, d[name]

    def is_used_group(self, group_name):
        for name, _ in self.iter_used_groups():
            if name == group_name:
                return True
        return False

    def add_units(self, *unit_names):
        """Add units to group.
        """
        for unit_name in unit_names:
            self._unit_names.add(unit_name)

        self.invalidate_members()

    @property
    def non_inherited_unit_names(self):
        return frozenset(self._unit_names)

    def remove_units(self, *unit_names):
        """Remove units from group.
        """
        for unit_name in unit_names:
            self._unit_names.remove(unit_name)

        self.invalidate_members()

    def add_groups(self, *group_names):
        """Add groups to group.
        """
        d = self._REGISTRY._groups
        for group_name in group_names:

            grp = d[group_name]

            if grp.is_used_group(self.name):
                raise ValueError(
                    "Cyclic relationship found between %s and %s"
                    % (self.name, group_name)
                )

            self._used_groups.add(group_name)
            grp._used_by.add(self.name)

        self.invalidate_members()

    def remove_groups(self, *group_names):
        """Remove groups from group.
        """
        d = self._REGISTRY._groups
        for group_name in group_names:
            grp = d[group_name]

            self._used_groups.remove(group_name)
            grp._used_by.remove(self.name)

        self.invalidate_members()

    @classmethod
    def from_lines(cls, lines, define_func, non_int_type=float):
        """Return a Group object parsing an iterable of lines.

        Parameters
        ----------
        lines : list[str]
            iterable
        define_func : callable
            Function to define a unit in the registry; it must accept a single string as
            a parameter.

        Returns
        -------

        """
        lines = SourceIterator(lines)
        lineno, header = next(lines)

        r = cls._header_re.search(header)

        if r is None:
            raise ValueError("Invalid Group header syntax: '%s'" % header)

        name = r.groupdict()["name"].strip()
        groups = r.groupdict()["used_groups"]
        if groups:
            group_names = tuple(a.strip() for a in groups.split(","))
        else:
            group_names = ()

        unit_names = []
        for lineno, line in lines:
            if "=" in line:
                # Is a definition
                definition = Definition.from_string(line, non_int_type=non_int_type)
                if not isinstance(definition, UnitDefinition):
                    raise DefinitionSyntaxError(
                        "Only UnitDefinition are valid inside _used_groups, not "
                        + str(definition),
                        lineno=lineno,
                    )

                try:
                    define_func(definition)
                except (RedefinitionError, DefinitionSyntaxError) as ex:
                    if ex.lineno is None:
                        ex.lineno = lineno
                    raise ex

                unit_names.append(definition.name)
            else:
                unit_names.append(line.strip())

        grp = cls(name)

        grp.add_units(*unit_names)

        if group_names:
            grp.add_groups(*group_names)

        return grp

    def __getattr__(self, item):
        getattr_maybe_raise(self, item)
        return self._REGISTRY


class System(SharedRegistryObject):
    """A system is a Group plus a set of base units.

    Members are computed dynamically, that is if a unit is added to a group X
    all groups that include X are affected.

    The System belongs to one Registry.

    It can be specified in the definition file as::

        @system <name> [using <group 1>, ..., <group N>]
            <rule 1>
            ...
            <rule N>
        @end

    The syntax for the rule is:

        new_unit_name : old_unit_name

    where:
        - old_unit_name: a root unit part which is going to be removed from the system.
        - new_unit_name: a non root unit which is going to replace the old_unit.

    If the new_unit_name and the old_unit_name, the later and the colon can be ommited.
    """

    #: Regex to match the header parts of a context.
    _header_re = re.compile(r"@system\s+(?P<name>\w+)\s*(using\s(?P<used_groups>.*))*")

    def __init__(self, name):
        """
        :param name: Name of the group
        :type name: str
        """

        #: Name of the system
        #: :type: str
        self.name = name

        #: Maps root unit names to a dict indicating the new unit and its exponent.
        #: :type: dict[str, dict[str, number]]]
        self.base_units = {}

        #: Derived unit names.
        #: :type: set(str)
        self.derived_units = set()

        #: Names of the _used_groups in used by this system.
        #: :type: set(str)
        self._used_groups = set()

        #: :type: frozenset | None
        self._computed_members = None

        # Add this system to the system dictionary
        self._REGISTRY._systems[self.name] = self

    def __dir__(self):
        return list(self.members)

    def __getattr__(self, item):
        getattr_maybe_raise(self, item)
        u = getattr(self._REGISTRY, self.name + "_" + item, None)
        if u is not None:
            return u
        return getattr(self._REGISTRY, item)

    @property
    def members(self):
        d = self._REGISTRY._groups
        if self._computed_members is None:
            self._computed_members = set()

            for group_name in self._used_groups:
                try:
                    self._computed_members |= d[group_name].members
                except KeyError:
                    logger.warning(
                        "Could not resolve {} in System {}".format(
                            group_name, self.name
                        )
                    )

            self._computed_members = frozenset(self._computed_members)

        return self._computed_members

    def invalidate_members(self):
        """Invalidate computed members in this Group and all parent nodes."""
        self._computed_members = None

    def add_groups(self, *group_names):
        """Add groups to group.
        """
        self._used_groups |= set(group_names)

        self.invalidate_members()

    def remove_groups(self, *group_names):
        """Remove groups from group.
        """
        self._used_groups -= set(group_names)

        self.invalidate_members()

    def format_babel(self, locale):
        """translate the name of the system.
        """
        if locale and self.name in _babel_systems:
            name = _babel_systems[self.name]
            locale = babel_parse(locale)
            return locale.measurement_systems[name]
        return self.name

    @classmethod
    def from_lines(cls, lines, get_root_func, non_int_type=float):
        lines = SourceIterator(lines)

        lineno, header = next(lines)

        r = cls._header_re.search(header)

        if r is None:
            raise ValueError("Invalid System header syntax '%s'" % header)

        name = r.groupdict()["name"].strip()
        groups = r.groupdict()["used_groups"]

        # If the systems has no group, it automatically uses the root group.
        if groups:
            group_names = tuple(a.strip() for a in groups.split(","))
        else:
            group_names = ("root",)

        base_unit_names = {}
        derived_unit_names = []
        for lineno, line in lines:
            line = line.strip()

            # We would identify a
            #  - old_unit: a root unit part which is going to be removed from the system.
            #  - new_unit: a non root unit which is going to replace the old_unit.

            if ":" in line:
                # The syntax is new_unit:old_unit

                new_unit, old_unit = line.split(":")
                new_unit, old_unit = new_unit.strip(), old_unit.strip()

                # The old unit MUST be a root unit, if not raise an error.
                if old_unit != str(get_root_func(old_unit)[1]):
                    raise ValueError(
                        "In `%s`, the unit at the right of the `:` must be a root unit."
                        % line
                    )

                # Here we find new_unit expanded in terms of root_units
                new_unit_expanded = to_units_container(
                    get_root_func(new_unit)[1], cls._REGISTRY
                )

                # We require that the old unit is present in the new_unit expanded
                if old_unit not in new_unit_expanded:
                    raise ValueError("Old unit must be a component of new unit")

                # Here we invert the equation, in other words
                # we write old units in terms new unit and expansion
                new_unit_dict = {
                    new_unit: -1 / value
                    for new_unit, value in new_unit_expanded.items()
                    if new_unit != old_unit
                }
                new_unit_dict[new_unit] = 1 / new_unit_expanded[old_unit]

                base_unit_names[old_unit] = new_unit_dict

            else:
                # The syntax is new_unit
                # old_unit is inferred as the root unit with the same dimensionality.

                new_unit = line
                old_unit_dict = to_units_container(get_root_func(line)[1])

                if len(old_unit_dict) != 1:
                    raise ValueError(
                        "The new base must be a root dimension if not discarded unit is specified."
                    )

                old_unit, value = dict(old_unit_dict).popitem()

                base_unit_names[old_unit] = {new_unit: 1 / value}

        system = cls(name)

        system.add_groups(*group_names)

        system.base_units.update(**base_unit_names)
        system.derived_units |= set(derived_unit_names)

        return system


class Lister:
    def __init__(self, d):
        self.d = d

    def __dir__(self):
        return list(self.d.keys())

    def __getattr__(self, item):
        getattr_maybe_raise(self, item)
        return self.d[item]


_Group = Group
_System = System


def build_group_class(registry):
    class Group(_Group):
        _REGISTRY = registry

    return Group


def build_system_class(registry):
    class System(_System):
        _REGISTRY = registry

    return System
