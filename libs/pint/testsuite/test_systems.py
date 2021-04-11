from pint import UnitRegistry
from pint.testsuite import QuantityTestCase


class TestGroup(QuantityTestCase):
    def _build_empty_reg_root(self):
        ureg = UnitRegistry(None)
        grp = ureg.get_group("root")
        grp.invalidate_members()
        return ureg, ureg.get_group("root")

    def test_units_programatically(self):
        ureg, root = self._build_empty_reg_root()
        d = ureg._groups

        self.assertEqual(root._used_groups, set())
        self.assertEqual(root._used_by, set())
        root.add_units("meter", "second", "meter")
        self.assertEqual(root._unit_names, {"meter", "second"})
        self.assertEqual(root.members, {"meter", "second"})

        self.assertEqual(d.keys(), {"root"})

    def test_cyclic(self):
        ureg, root = self._build_empty_reg_root()
        g2 = ureg.Group("g2")
        g3 = ureg.Group("g3")
        g2.add_groups("g3")

        self.assertRaises(ValueError, g2.add_groups, "root")
        self.assertRaises(ValueError, g3.add_groups, "g2")
        self.assertRaises(ValueError, g3.add_groups, "root")

    def test_groups_programatically(self):
        ureg, root = self._build_empty_reg_root()
        d = ureg._groups
        g2 = ureg.Group("g2")

        self.assertEqual(d.keys(), {"root", "g2"})

        self.assertEqual(root._used_groups, {"g2"})
        self.assertEqual(root._used_by, set())

        self.assertEqual(g2._used_groups, set())
        self.assertEqual(g2._used_by, {"root"})

    def test_simple(self):
        lines = ["@group mygroup", "meter", "second"]

        ureg, root = self._build_empty_reg_root()
        d = ureg._groups

        grp = ureg.Group.from_lines(lines, lambda x: None)

        self.assertEqual(d.keys(), {"root", "mygroup"})

        self.assertEqual(grp.name, "mygroup")
        self.assertEqual(grp._unit_names, {"meter", "second"})
        self.assertEqual(grp._used_groups, set())
        self.assertEqual(grp._used_by, {root.name})
        self.assertEqual(grp.members, frozenset(["meter", "second"]))

    def test_using1(self):
        lines = ["@group mygroup using group1", "meter", "second"]

        ureg, root = self._build_empty_reg_root()
        ureg.Group("group1")
        grp = ureg.Group.from_lines(lines, lambda x: None)
        self.assertEqual(grp.name, "mygroup")
        self.assertEqual(grp._unit_names, {"meter", "second"})
        self.assertEqual(grp._used_groups, {"group1"})
        self.assertEqual(grp.members, frozenset(["meter", "second"]))

    def test_using2(self):
        lines = ["@group mygroup using group1,group2", "meter", "second"]

        ureg, root = self._build_empty_reg_root()
        ureg.Group("group1")
        ureg.Group("group2")
        grp = ureg.Group.from_lines(lines, lambda x: None)
        self.assertEqual(grp.name, "mygroup")
        self.assertEqual(grp._unit_names, {"meter", "second"})
        self.assertEqual(grp._used_groups, {"group1", "group2"})
        self.assertEqual(grp.members, frozenset(["meter", "second"]))

    def test_spaces(self):
        lines = ["@group   mygroup   using   group1 , group2", " meter ", " second  "]

        ureg, root = self._build_empty_reg_root()
        ureg.Group("group1")
        ureg.Group("group2")
        grp = ureg.Group.from_lines(lines, lambda x: None)
        self.assertEqual(grp.name, "mygroup")
        self.assertEqual(grp._unit_names, {"meter", "second"})
        self.assertEqual(grp._used_groups, {"group1", "group2"})
        self.assertEqual(grp.members, frozenset(["meter", "second"]))

    def test_invalidate_members(self):
        lines = ["@group mygroup using group1", "meter", "second"]

        ureg, root = self._build_empty_reg_root()
        ureg.Group("group1")
        grp = ureg.Group.from_lines(lines, lambda x: None)
        self.assertIs(root._computed_members, None)
        self.assertIs(grp._computed_members, None)
        self.assertEqual(grp.members, frozenset(["meter", "second"]))
        self.assertIs(root._computed_members, None)
        self.assertIsNot(grp._computed_members, None)
        self.assertEqual(root.members, frozenset(["meter", "second"]))
        self.assertIsNot(root._computed_members, None)
        self.assertIsNot(grp._computed_members, None)
        grp.invalidate_members()
        self.assertIs(root._computed_members, None)
        self.assertIs(grp._computed_members, None)

    def test_with_defintions(self):
        lines = [
            "@group imperial",
            "inch",
            "yard",
            "kings_leg = 2 * meter",
            "kings_head = 52 * inch" "pint",
        ]
        defs = []

        def define(ud):
            defs.append(ud.name)

        ureg, root = self._build_empty_reg_root()
        ureg.Group.from_lines(lines, define)

        self.assertEqual(["kings_leg", "kings_head"], defs)

    def test_members_including(self):
        ureg, root = self._build_empty_reg_root()

        g1 = ureg.Group("group1")
        g1.add_units("second", "inch")

        g2 = ureg.Group("group2")
        g2.add_units("second", "newton")

        g3 = ureg.Group("group3")
        g3.add_units("meter", "second")
        g3.add_groups("group1", "group2")

        self.assertEqual(root.members, frozenset(["meter", "second", "newton", "inch"]))
        self.assertEqual(g1.members, frozenset(["second", "inch"]))
        self.assertEqual(g2.members, frozenset(["second", "newton"]))
        self.assertEqual(g3.members, frozenset(["meter", "second", "newton", "inch"]))

    def test_get_compatible_units(self):
        ureg = UnitRegistry()

        g = ureg.get_group("test-imperial")
        g.add_units("inch", "yard", "pint")
        c = ureg.get_compatible_units("meter", "test-imperial")
        self.assertEqual(c, frozenset([ureg.inch, ureg.yard]))


class TestSystem(QuantityTestCase):
    def _build_empty_reg_root(self):
        ureg = UnitRegistry(None)
        grp = ureg.get_group("root")
        grp.invalidate_members()
        return ureg, ureg.get_group("root")

    def test_implicit_root(self):
        lines = ["@system mks", "meter", "kilogram", "second"]

        ureg, root = self._build_empty_reg_root()
        s = ureg.System.from_lines(lines, lambda x: x)
        s._used_groups = {"root"}

    def test_simple_using(self):
        lines = ["@system mks using g1", "meter", "kilogram", "second"]

        ureg, root = self._build_empty_reg_root()
        s = ureg.System.from_lines(lines, lambda x: x)
        s._used_groups = {"root", "g1"}

    def test_members_group(self):
        lines = ["@system mk", "meter", "kilogram"]

        ureg, root = self._build_empty_reg_root()
        root.add_units("second")
        s = ureg.System.from_lines(lines, lambda x: x)
        self.assertEqual(s.members, frozenset(["second"]))

    def test_get_compatible_units(self):
        sysname = "mysys1"
        ureg = UnitRegistry()

        g = ureg.get_group("test-imperial")

        g.add_units("inch", "yard", "pint")
        c = ureg.get_compatible_units("meter", "test-imperial")
        self.assertEqual(c, frozenset([ureg.inch, ureg.yard]))

        lines = ["@system %s using test-imperial" % sysname, "inch"]

        ureg.System.from_lines(lines, lambda x: x)
        c = ureg.get_compatible_units("meter", sysname)
        self.assertEqual(c, frozenset([ureg.inch, ureg.yard]))

    def test_get_base_units(self):
        sysname = "mysys2"
        ureg = UnitRegistry()

        g = ureg.get_group("test-imperial")
        g.add_units("inch", "yard", "pint")

        lines = ["@system %s using test-imperial" % sysname, "inch"]

        s = ureg.System.from_lines(lines, ureg.get_base_units)
        ureg._systems[s.name] = s

        # base_factor, destination_units
        c = ureg.get_base_units("inch", system=sysname)
        self.assertAlmostEqual(c[0], 1)
        self.assertEqual(c[1], {"inch": 1})

        c = ureg.get_base_units("cm", system=sysname)
        self.assertAlmostEqual(c[0], 1.0 / 2.54)
        self.assertEqual(c[1], {"inch": 1})

    def test_get_base_units_different_exponent(self):
        sysname = "mysys3"
        ureg = UnitRegistry()

        g = ureg.get_group("test-imperial")
        g.add_units("inch", "yard", "pint")
        ureg.get_compatible_units("meter", "test-imperial")

        lines = ["@system %s using test-imperial" % sysname, "pint:meter"]

        s = ureg.System.from_lines(lines, ureg.get_base_units)
        ureg._systems[s.name] = s

        # base_factor, destination_units
        c = ureg.get_base_units("inch", system=sysname)
        self.assertAlmostEqual(c[0], 0.326, places=3)
        self.assertEqual(c[1], {"pint": 1.0 / 3})

        c = ureg.get_base_units("cm", system=sysname)
        self.assertAlmostEqual(c[0], 0.1283, places=3)
        self.assertEqual(c[1], {"pint": 1.0 / 3})

        c = ureg.get_base_units("inch**2", system=sysname)
        self.assertAlmostEqual(c[0], 0.326 ** 2, places=3)
        self.assertEqual(c[1], {"pint": 2.0 / 3})

        c = ureg.get_base_units("cm**2", system=sysname)
        self.assertAlmostEqual(c[0], 0.1283 ** 2, places=3)
        self.assertEqual(c[1], {"pint": 2.0 / 3})

    def test_get_base_units_relation(self):
        sysname = "mysys4"
        ureg = UnitRegistry()

        g = ureg.get_group("test-imperial")
        g.add_units("inch", "yard", "pint")

        lines = ["@system %s using test-imperial" % sysname, "mph:meter"]

        s = ureg.System.from_lines(lines, ureg.get_base_units)
        ureg._systems[s.name] = s
        # base_factor, destination_units
        c = ureg.get_base_units("inch", system=sysname)
        self.assertAlmostEqual(c[0], 0.056, places=2)
        self.assertEqual(c[1], {"mph": 1, "second": 1})

        c = ureg.get_base_units("kph", system=sysname)
        self.assertAlmostEqual(c[0], 0.6213, places=3)
        self.assertEqual(c[1], {"mph": 1})

    def test_members_nowarning(self):
        ureg = self.ureg
        for name in dir(ureg.sys):
            dir(getattr(ureg.sys, name))
