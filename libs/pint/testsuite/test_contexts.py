import itertools
import math
from collections import defaultdict

from pint import (
    DefinitionSyntaxError,
    DimensionalityError,
    UndefinedUnitError,
    UnitRegistry,
)
from pint.context import Context
from pint.testsuite import QuantityTestCase
from pint.util import UnitsContainer


def add_ctxs(ureg):
    a, b = UnitsContainer({"[length]": 1}), UnitsContainer({"[time]": -1})
    d = Context("lc")
    d.add_transformation(a, b, lambda ureg, x: ureg.speed_of_light / x)
    d.add_transformation(b, a, lambda ureg, x: ureg.speed_of_light / x)

    ureg.add_context(d)

    a, b = UnitsContainer({"[length]": 1}), UnitsContainer({"[current]": 1})
    d = Context("ab")
    d.add_transformation(a, b, lambda ureg, x: ureg.ampere * ureg.meter / x)
    d.add_transformation(b, a, lambda ureg, x: ureg.ampere * ureg.meter / x)

    ureg.add_context(d)


def add_arg_ctxs(ureg):
    a, b = UnitsContainer({"[length]": 1}), UnitsContainer({"[time]": -1})
    d = Context("lc")
    d.add_transformation(a, b, lambda ureg, x, n: ureg.speed_of_light / x / n)
    d.add_transformation(b, a, lambda ureg, x, n: ureg.speed_of_light / x / n)

    ureg.add_context(d)

    a, b = UnitsContainer({"[length]": 1}), UnitsContainer({"[current]": 1})
    d = Context("ab")
    d.add_transformation(a, b, lambda ureg, x: ureg.ampere * ureg.meter / x)
    d.add_transformation(b, a, lambda ureg, x: ureg.ampere * ureg.meter / x)

    ureg.add_context(d)


def add_argdef_ctxs(ureg):
    a, b = UnitsContainer({"[length]": 1}), UnitsContainer({"[time]": -1})
    d = Context("lc", defaults=dict(n=1))
    assert d.defaults == dict(n=1)

    d.add_transformation(a, b, lambda ureg, x, n: ureg.speed_of_light / x / n)
    d.add_transformation(b, a, lambda ureg, x, n: ureg.speed_of_light / x / n)

    ureg.add_context(d)

    a, b = UnitsContainer({"[length]": 1}), UnitsContainer({"[current]": 1})
    d = Context("ab")
    d.add_transformation(a, b, lambda ureg, x: ureg.ampere * ureg.meter / x)
    d.add_transformation(b, a, lambda ureg, x: ureg.ampere * ureg.meter / x)

    ureg.add_context(d)


def add_sharedargdef_ctxs(ureg):
    a, b = UnitsContainer({"[length]": 1}), UnitsContainer({"[time]": -1})
    d = Context("lc", defaults=dict(n=1))
    assert d.defaults == dict(n=1)

    d.add_transformation(a, b, lambda ureg, x, n: ureg.speed_of_light / x / n)
    d.add_transformation(b, a, lambda ureg, x, n: ureg.speed_of_light / x / n)

    ureg.add_context(d)

    a, b = UnitsContainer({"[length]": 1}), UnitsContainer({"[current]": 1})
    d = Context("ab", defaults=dict(n=0))
    d.add_transformation(a, b, lambda ureg, x, n: ureg.ampere * ureg.meter * n / x)
    d.add_transformation(b, a, lambda ureg, x, n: ureg.ampere * ureg.meter * n / x)

    ureg.add_context(d)


class TestContexts(QuantityTestCase):
    def test_known_context(self):
        ureg = UnitRegistry()
        add_ctxs(ureg)
        with ureg.context("lc"):
            self.assertTrue(ureg._active_ctx)
            self.assertTrue(ureg._active_ctx.graph)

        self.assertFalse(ureg._active_ctx)
        self.assertFalse(ureg._active_ctx.graph)

        with ureg.context("lc", n=1):
            self.assertTrue(ureg._active_ctx)
            self.assertTrue(ureg._active_ctx.graph)

        self.assertFalse(ureg._active_ctx)
        self.assertFalse(ureg._active_ctx.graph)

    def test_known_context_enable(self):
        ureg = UnitRegistry()
        add_ctxs(ureg)
        ureg.enable_contexts("lc")
        self.assertTrue(ureg._active_ctx)
        self.assertTrue(ureg._active_ctx.graph)
        ureg.disable_contexts(1)

        self.assertFalse(ureg._active_ctx)
        self.assertFalse(ureg._active_ctx.graph)

        ureg.enable_contexts("lc", n=1)
        self.assertTrue(ureg._active_ctx)
        self.assertTrue(ureg._active_ctx.graph)
        ureg.disable_contexts(1)

        self.assertFalse(ureg._active_ctx)
        self.assertFalse(ureg._active_ctx.graph)

    def test_graph(self):
        ureg = UnitRegistry()
        add_ctxs(ureg)
        l = UnitsContainer({"[length]": 1.0})  # noqa: E741
        t = UnitsContainer({"[time]": -1.0})
        c = UnitsContainer({"[current]": 1.0})

        g_sp = defaultdict(set)
        g_sp.update({l: {t}, t: {l}})

        g_ab = defaultdict(set)
        g_ab.update({l: {c}, c: {l}})

        g = defaultdict(set)
        g.update({l: {t, c}, t: {l}, c: {l}})

        with ureg.context("lc"):
            self.assertEqual(ureg._active_ctx.graph, g_sp)

        with ureg.context("lc", n=1):
            self.assertEqual(ureg._active_ctx.graph, g_sp)

        with ureg.context("ab"):
            self.assertEqual(ureg._active_ctx.graph, g_ab)

        with ureg.context("lc"):
            with ureg.context("ab"):
                self.assertEqual(ureg._active_ctx.graph, g)

        with ureg.context("ab"):
            with ureg.context("lc"):
                self.assertEqual(ureg._active_ctx.graph, g)

        with ureg.context("lc", "ab"):
            self.assertEqual(ureg._active_ctx.graph, g)

        with ureg.context("ab", "lc"):
            self.assertEqual(ureg._active_ctx.graph, g)

    def test_graph_enable(self):
        ureg = UnitRegistry()
        add_ctxs(ureg)
        l = UnitsContainer({"[length]": 1.0})  # noqa: E741
        t = UnitsContainer({"[time]": -1.0})
        c = UnitsContainer({"[current]": 1.0})

        g_sp = defaultdict(set)
        g_sp.update({l: {t}, t: {l}})

        g_ab = defaultdict(set)
        g_ab.update({l: {c}, c: {l}})

        g = defaultdict(set)
        g.update({l: {t, c}, t: {l}, c: {l}})

        ureg.enable_contexts("lc")
        self.assertEqual(ureg._active_ctx.graph, g_sp)
        ureg.disable_contexts(1)

        ureg.enable_contexts("lc", n=1)
        self.assertEqual(ureg._active_ctx.graph, g_sp)
        ureg.disable_contexts(1)

        ureg.enable_contexts("ab")
        self.assertEqual(ureg._active_ctx.graph, g_ab)
        ureg.disable_contexts(1)

        ureg.enable_contexts("lc")
        ureg.enable_contexts("ab")
        self.assertEqual(ureg._active_ctx.graph, g)
        ureg.disable_contexts(2)

        ureg.enable_contexts("ab")
        ureg.enable_contexts("lc")
        self.assertEqual(ureg._active_ctx.graph, g)
        ureg.disable_contexts(2)

        ureg.enable_contexts("lc", "ab")
        self.assertEqual(ureg._active_ctx.graph, g)
        ureg.disable_contexts(2)

        ureg.enable_contexts("ab", "lc")
        self.assertEqual(ureg._active_ctx.graph, g)
        ureg.disable_contexts(2)

    def test_known_nested_context(self):
        ureg = UnitRegistry()
        add_ctxs(ureg)

        with ureg.context("lc"):
            x = dict(ureg._active_ctx)
            y = dict(ureg._active_ctx.graph)
            self.assertTrue(ureg._active_ctx)
            self.assertTrue(ureg._active_ctx.graph)

            with ureg.context("ab"):
                self.assertTrue(ureg._active_ctx)
                self.assertTrue(ureg._active_ctx.graph)
                self.assertNotEqual(x, ureg._active_ctx)
                self.assertNotEqual(y, ureg._active_ctx.graph)

            self.assertEqual(x, ureg._active_ctx)
            self.assertEqual(y, ureg._active_ctx.graph)

        self.assertFalse(ureg._active_ctx)
        self.assertFalse(ureg._active_ctx.graph)

    def test_unknown_context(self):
        ureg = UnitRegistry()
        add_ctxs(ureg)
        with self.assertRaises(KeyError):
            with ureg.context("la"):
                pass
        self.assertFalse(ureg._active_ctx)
        self.assertFalse(ureg._active_ctx.graph)

    def test_unknown_nested_context(self):
        ureg = UnitRegistry()
        add_ctxs(ureg)

        with ureg.context("lc"):
            x = dict(ureg._active_ctx)
            y = dict(ureg._active_ctx.graph)
            with self.assertRaises(KeyError):
                with ureg.context("la"):
                    pass

            self.assertEqual(x, ureg._active_ctx)
            self.assertEqual(y, ureg._active_ctx.graph)

        self.assertFalse(ureg._active_ctx)
        self.assertFalse(ureg._active_ctx.graph)

    def test_one_context(self):
        ureg = UnitRegistry()

        add_ctxs(ureg)

        q = 500 * ureg.meter
        s = (ureg.speed_of_light / q).to("Hz")

        meter_units = ureg.get_compatible_units(ureg.meter)
        hertz_units = ureg.get_compatible_units(ureg.hertz)

        self.assertRaises(DimensionalityError, q.to, "Hz")
        with ureg.context("lc"):
            self.assertEqual(q.to("Hz"), s)
            self.assertEqual(ureg.get_compatible_units(q), meter_units | hertz_units)
        self.assertRaises(DimensionalityError, q.to, "Hz")
        self.assertEqual(ureg.get_compatible_units(q), meter_units)

    def test_multiple_context(self):
        ureg = UnitRegistry()

        add_ctxs(ureg)

        q = 500 * ureg.meter
        s = (ureg.speed_of_light / q).to("Hz")

        meter_units = ureg.get_compatible_units(ureg.meter)
        hertz_units = ureg.get_compatible_units(ureg.hertz)
        ampere_units = ureg.get_compatible_units(ureg.ampere)

        self.assertRaises(DimensionalityError, q.to, "Hz")
        with ureg.context("lc", "ab"):
            self.assertEqual(q.to("Hz"), s)
            self.assertEqual(
                ureg.get_compatible_units(q), meter_units | hertz_units | ampere_units
            )
        self.assertRaises(DimensionalityError, q.to, "Hz")
        self.assertEqual(ureg.get_compatible_units(q), meter_units)

    def test_nested_context(self):
        ureg = UnitRegistry()

        add_ctxs(ureg)

        q = 500 * ureg.meter
        s = (ureg.speed_of_light / q).to("Hz")

        self.assertRaises(DimensionalityError, q.to, "Hz")
        with ureg.context("lc"):
            self.assertEqual(q.to("Hz"), s)
            with ureg.context("ab"):
                self.assertEqual(q.to("Hz"), s)
            self.assertEqual(q.to("Hz"), s)

        with ureg.context("ab"):
            self.assertRaises(DimensionalityError, q.to, "Hz")
            with ureg.context("lc"):
                self.assertEqual(q.to("Hz"), s)
            self.assertRaises(DimensionalityError, q.to, "Hz")

    def test_context_with_arg(self):

        ureg = UnitRegistry()

        add_arg_ctxs(ureg)

        q = 500 * ureg.meter
        s = (ureg.speed_of_light / q).to("Hz")

        self.assertRaises(DimensionalityError, q.to, "Hz")
        with ureg.context("lc", n=1):
            self.assertEqual(q.to("Hz"), s)
            with ureg.context("ab"):
                self.assertEqual(q.to("Hz"), s)
            self.assertEqual(q.to("Hz"), s)

        with ureg.context("ab"):
            self.assertRaises(DimensionalityError, q.to, "Hz")
            with ureg.context("lc", n=1):
                self.assertEqual(q.to("Hz"), s)
            self.assertRaises(DimensionalityError, q.to, "Hz")

        with ureg.context("lc"):
            self.assertRaises(TypeError, q.to, "Hz")

    def test_enable_context_with_arg(self):

        ureg = UnitRegistry()

        add_arg_ctxs(ureg)

        q = 500 * ureg.meter
        s = (ureg.speed_of_light / q).to("Hz")

        self.assertRaises(DimensionalityError, q.to, "Hz")
        ureg.enable_contexts("lc", n=1)
        self.assertEqual(q.to("Hz"), s)
        ureg.enable_contexts("ab")
        self.assertEqual(q.to("Hz"), s)
        self.assertEqual(q.to("Hz"), s)
        ureg.disable_contexts(1)
        ureg.disable_contexts(1)

        ureg.enable_contexts("ab")
        self.assertRaises(DimensionalityError, q.to, "Hz")
        ureg.enable_contexts("lc", n=1)
        self.assertEqual(q.to("Hz"), s)
        ureg.disable_contexts(1)
        self.assertRaises(DimensionalityError, q.to, "Hz")
        ureg.disable_contexts(1)

        ureg.enable_contexts("lc")
        self.assertRaises(TypeError, q.to, "Hz")
        ureg.disable_contexts(1)

    def test_context_with_arg_def(self):

        ureg = UnitRegistry()

        add_argdef_ctxs(ureg)

        q = 500 * ureg.meter
        s = (ureg.speed_of_light / q).to("Hz")

        self.assertRaises(DimensionalityError, q.to, "Hz")
        with ureg.context("lc"):
            self.assertEqual(q.to("Hz"), s)
            with ureg.context("ab"):
                self.assertEqual(q.to("Hz"), s)
            self.assertEqual(q.to("Hz"), s)

        with ureg.context("ab"):
            self.assertRaises(DimensionalityError, q.to, "Hz")
            with ureg.context("lc"):
                self.assertEqual(q.to("Hz"), s)
            self.assertRaises(DimensionalityError, q.to, "Hz")

        self.assertRaises(DimensionalityError, q.to, "Hz")
        with ureg.context("lc", n=2):
            self.assertEqual(q.to("Hz"), s / 2)
            with ureg.context("ab"):
                self.assertEqual(q.to("Hz"), s / 2)
            self.assertEqual(q.to("Hz"), s / 2)

        with ureg.context("ab"):
            self.assertRaises(DimensionalityError, q.to, "Hz")
            with ureg.context("lc", n=2):
                self.assertEqual(q.to("Hz"), s / 2)
            self.assertRaises(DimensionalityError, q.to, "Hz")

    def test_context_with_sharedarg_def(self):

        ureg = UnitRegistry()

        add_sharedargdef_ctxs(ureg)

        q = 500 * ureg.meter
        s = (ureg.speed_of_light / q).to("Hz")
        u = (1 / 500) * ureg.ampere

        with ureg.context("lc"):
            self.assertEqual(q.to("Hz"), s)
            with ureg.context("ab"):
                self.assertEqual(q.to("ampere"), u)

        with ureg.context("ab"):
            self.assertEqual(q.to("ampere"), 0 * u)
            with ureg.context("lc"):
                self.assertRaises(ZeroDivisionError, ureg.Quantity.to, q, "Hz")

        with ureg.context("lc", n=2):
            self.assertEqual(q.to("Hz"), s / 2)
            with ureg.context("ab"):
                self.assertEqual(q.to("ampere"), 2 * u)

        with ureg.context("ab", n=3):
            self.assertEqual(q.to("ampere"), 3 * u)
            with ureg.context("lc"):
                self.assertEqual(q.to("Hz"), s / 3)

        with ureg.context("lc", n=2):
            self.assertEqual(q.to("Hz"), s / 2)
            with ureg.context("ab", n=4):
                self.assertEqual(q.to("ampere"), 4 * u)

        with ureg.context("ab", n=3):
            self.assertEqual(q.to("ampere"), 3 * u)
            with ureg.context("lc", n=6):
                self.assertEqual(q.to("Hz"), s / 6)

    def test_anonymous_context(self):
        ureg = UnitRegistry()
        c = Context()
        c.add_transformation("[length]", "[time]", lambda ureg, x: x / ureg("5 cm/s"))
        self.assertRaises(ValueError, ureg.add_context, c)

        x = ureg("10 cm")
        expect = ureg("2 s")
        self.assertQuantityEqual(x.to("s", c), expect)

        with ureg.context(c):
            self.assertQuantityEqual(x.to("s"), expect)

        ureg.enable_contexts(c)
        self.assertQuantityEqual(x.to("s"), expect)
        ureg.disable_contexts(1)
        self.assertRaises(DimensionalityError, x.to, "s")

        # Multiple anonymous contexts
        c2 = Context()
        c2.add_transformation("[length]", "[time]", lambda ureg, x: x / ureg("10 cm/s"))
        c2.add_transformation("[mass]", "[time]", lambda ureg, x: x / ureg("10 kg/s"))
        with ureg.context(c2, c):
            self.assertQuantityEqual(x.to("s"), expect)
            # Transformations only in c2 are still working even if c takes priority
            self.assertQuantityEqual(ureg("100 kg").to("s"), ureg("10 s"))
        with ureg.context(c, c2):
            self.assertQuantityEqual(x.to("s"), ureg("1 s"))

    def _test_ctx(self, ctx):
        ureg = UnitRegistry()
        q = 500 * ureg.meter
        s = (ureg.speed_of_light / q).to("Hz")

        nctx = len(ureg._contexts)

        self.assertNotIn(ctx.name, ureg._contexts)
        ureg.add_context(ctx)

        self.assertIn(ctx.name, ureg._contexts)
        self.assertEqual(len(ureg._contexts), nctx + 1 + len(ctx.aliases))

        with ureg.context(ctx.name):
            self.assertEqual(q.to("Hz"), s)
            self.assertEqual(s.to("meter"), q)

        ureg.remove_context(ctx.name)
        self.assertNotIn(ctx.name, ureg._contexts)
        self.assertEqual(len(ureg._contexts), nctx)

    def test_parse_invalid(self):
        for badrow in (
            "[length] = 1 / [time]: c / value",
            "1 / [time] = [length]: c / value",
            "[length] <- [time] = c / value",
            "[length] - [time] = c / value",
        ):
            with self.subTest(badrow):
                with self.assertRaises(DefinitionSyntaxError):
                    Context.from_lines(["@context c", badrow])

    def test_parse_simple(self):

        a = Context.__keytransform__(
            UnitsContainer({"[time]": -1}), UnitsContainer({"[length]": 1})
        )
        b = Context.__keytransform__(
            UnitsContainer({"[length]": 1}), UnitsContainer({"[time]": -1})
        )

        s = [
            "@context longcontextname",
            "[length] -> 1 / [time]: c / value",
            "1 / [time] -> [length]: c / value",
        ]

        c = Context.from_lines(s)
        self.assertEqual(c.name, "longcontextname")
        self.assertEqual(c.aliases, ())
        self.assertEqual(c.defaults, {})
        self.assertEqual(c.funcs.keys(), {a, b})
        self._test_ctx(c)

        s = ["@context longcontextname = lc", "[length] <-> 1 / [time]: c / value"]

        c = Context.from_lines(s)
        self.assertEqual(c.name, "longcontextname")
        self.assertEqual(c.aliases, ("lc",))
        self.assertEqual(c.defaults, {})
        self.assertEqual(c.funcs.keys(), {a, b})
        self._test_ctx(c)

        s = [
            "@context longcontextname = lc = lcn",
            "[length] <-> 1 / [time]: c / value",
        ]

        c = Context.from_lines(s)
        self.assertEqual(c.name, "longcontextname")
        self.assertEqual(c.aliases, ("lc", "lcn"))
        self.assertEqual(c.defaults, {})
        self.assertEqual(c.funcs.keys(), {a, b})
        self._test_ctx(c)

    def test_parse_auto_inverse(self):

        a = Context.__keytransform__(
            UnitsContainer({"[time]": -1.0}), UnitsContainer({"[length]": 1.0})
        )
        b = Context.__keytransform__(
            UnitsContainer({"[length]": 1.0}), UnitsContainer({"[time]": -1.0})
        )

        s = ["@context longcontextname", "[length] <-> 1 / [time]: c / value"]

        c = Context.from_lines(s)
        self.assertEqual(c.defaults, {})
        self.assertEqual(c.funcs.keys(), {a, b})
        self._test_ctx(c)

    def test_parse_define(self):
        a = Context.__keytransform__(
            UnitsContainer({"[time]": -1}), UnitsContainer({"[length]": 1.0})
        )
        b = Context.__keytransform__(
            UnitsContainer({"[length]": 1}), UnitsContainer({"[time]": -1.0})
        )

        s = ["@context longcontextname", "[length] <-> 1 / [time]: c / value"]
        c = Context.from_lines(s)
        self.assertEqual(c.defaults, {})
        self.assertEqual(c.funcs.keys(), {a, b})
        self._test_ctx(c)

    def test_parse_parameterized(self):
        a = Context.__keytransform__(
            UnitsContainer({"[time]": -1.0}), UnitsContainer({"[length]": 1.0})
        )
        b = Context.__keytransform__(
            UnitsContainer({"[length]": 1.0}), UnitsContainer({"[time]": -1.0})
        )

        s = ["@context(n=1) longcontextname", "[length] <-> 1 / [time]: n * c / value"]

        c = Context.from_lines(s)
        self.assertEqual(c.defaults, {"n": 1})
        self.assertEqual(c.funcs.keys(), {a, b})
        self._test_ctx(c)

        s = [
            "@context(n=1, bla=2) longcontextname",
            "[length] <-> 1 / [time]: n * c / value / bla",
        ]

        c = Context.from_lines(s)
        self.assertEqual(c.defaults, {"n": 1, "bla": 2})
        self.assertEqual(c.funcs.keys(), {a, b})

        # If the variable is not present in the definition, then raise an error
        s = ["@context(n=1) longcontextname", "[length] <-> 1 / [time]: c / value"]
        self.assertRaises(DefinitionSyntaxError, Context.from_lines, s)

    def test_warnings(self):

        ureg = UnitRegistry()

        with self.capture_log() as buffer:
            add_ctxs(ureg)

            d = Context("ab")
            ureg.add_context(d)

            self.assertEqual(len(buffer), 1)
            self.assertIn("ab", str(buffer[-1]))

            d = Context("ab1", aliases=("ab",))
            ureg.add_context(d)

            self.assertEqual(len(buffer), 2)
            self.assertIn("ab", str(buffer[-1]))


class TestDefinedContexts(QuantityTestCase):

    FORCE_NDARRAY = False

    def test_defined(self):
        ureg = self.ureg
        with ureg.context("sp"):
            pass

        a = Context.__keytransform__(
            UnitsContainer({"[time]": -1.0}), UnitsContainer({"[length]": 1.0})
        )
        b = Context.__keytransform__(
            UnitsContainer({"[length]": 1.0}), UnitsContainer({"[time]": -1.0})
        )
        self.assertIn(a, ureg._contexts["sp"].funcs)
        self.assertIn(b, ureg._contexts["sp"].funcs)
        with ureg.context("sp"):
            self.assertIn(a, ureg._active_ctx)
            self.assertIn(b, ureg._active_ctx)

    def test_spectroscopy(self):
        ureg = self.ureg
        eq = (532.0 * ureg.nm, 563.5 * ureg.terahertz, 2.33053 * ureg.eV)
        with ureg.context("sp"):
            from pint.util import find_shortest_path

            for a, b in itertools.product(eq, eq):
                for x in range(2):
                    if x == 1:
                        a = a.to_base_units()
                        b = b.to_base_units()
                    da, db = Context.__keytransform__(
                        a.dimensionality, b.dimensionality
                    )
                    p = find_shortest_path(ureg._active_ctx.graph, da, db)
                    self.assertTrue(p)
                    msg = "{} <-> {}".format(a, b)
                    # assertAlmostEqualRelError converts second to first
                    self.assertQuantityAlmostEqual(b, a, rtol=0.01, msg=msg)

        for a, b in itertools.product(eq, eq):
            self.assertQuantityAlmostEqual(a.to(b.units, "sp"), b, rtol=0.01)

    def test_textile(self):
        ureg = self.ureg
        qty_direct = 1.331 * ureg.tex
        with self.assertRaises(DimensionalityError):
            qty_indirect = qty_direct.to("Nm")

        with ureg.context("textile"):
            from pint.util import find_shortest_path

            qty_indirect = qty_direct.to("Nm")
            a = qty_direct.to_base_units()
            b = qty_indirect.to_base_units()
            da, db = Context.__keytransform__(a.dimensionality, b.dimensionality)
            p = find_shortest_path(ureg._active_ctx.graph, da, db)
            self.assertTrue(p)
            msg = "{} <-> {}".format(a, b)
            self.assertQuantityAlmostEqual(b, a, rtol=0.01, msg=msg)

            # Check RKM <-> cN/tex conversion
            self.assertQuantityAlmostEqual(1 * ureg.RKM, 0.980665 * ureg.cN / ureg.tex)
            self.assertQuantityAlmostEqual(
                (1 / 0.980665) * ureg.RKM, 1 * ureg.cN / ureg.tex
            )
            self.assertAlmostEqual((1 * ureg.RKM).to(ureg.cN / ureg.tex).m, 0.980665)
            self.assertAlmostEqual(
                (1 * ureg.cN / ureg.tex).to(ureg.RKM).m, 1 / 0.980665
            )

    def test_decorator(self):
        ureg = self.ureg

        a = 532.0 * ureg.nm
        with ureg.context("sp"):
            b = a.to("terahertz")

        def f(wl):
            return wl.to("terahertz")

        self.assertRaises(DimensionalityError, f, a)

        @ureg.with_context("sp")
        def g(wl):
            return wl.to("terahertz")

        self.assertEqual(b, g(a))

    def test_decorator_composition(self):
        ureg = self.ureg

        a = 532.0 * ureg.nm
        with ureg.context("sp"):
            b = a.to("terahertz")

        @ureg.with_context("sp")
        @ureg.check("[length]")
        def f(wl):
            return wl.to("terahertz")

        @ureg.with_context("sp")
        @ureg.check("[length]")
        def g(wl):
            return wl.to("terahertz")

        self.assertEqual(b, f(a))
        self.assertEqual(b, g(a))


class TestContextRedefinitions(QuantityTestCase):
    def test_redefine(self):
        ureg = UnitRegistry(
            """
            foo = [d] = f = foo_alias
            bar = 2 foo = b = bar_alias
            baz = 3 bar = _ = baz_alias
            asd = 4 baz

            @context c
                # Note how we're redefining a symbol, not the base name, as a
                # function of another name
                b = 5 f
            """.splitlines()
        )
        # Units that are somehow directly or indirectly defined as a function of the
        # overridden unit are also affected
        foo = ureg.Quantity(1, "foo")
        bar = ureg.Quantity(1, "bar")
        asd = ureg.Quantity(1, "asd")

        # Test without context before and after, to verify that the cache and units have
        # not been polluted
        for enable_ctx in (False, True, False):
            with self.subTest(enable_ctx):
                if enable_ctx:
                    ureg.enable_contexts("c")
                    k = 5
                else:
                    k = 2

                self.assertEqual(foo.to("b").magnitude, 1 / k)
                self.assertEqual(foo.to("bar").magnitude, 1 / k)
                self.assertEqual(foo.to("bar_alias").magnitude, 1 / k)
                self.assertEqual(foo.to("baz").magnitude, 1 / k / 3)
                self.assertEqual(bar.to("foo").magnitude, k)
                self.assertEqual(bar.to("baz").magnitude, 1 / 3)
                self.assertEqual(asd.to("foo").magnitude, 4 * 3 * k)
                self.assertEqual(asd.to("bar").magnitude, 4 * 3)
                self.assertEqual(asd.to("baz").magnitude, 4)

            ureg.disable_contexts()

    def test_define_nan(self):
        ureg = UnitRegistry(
            """
            USD = [currency]
            EUR = nan USD
            GBP = nan USD

            @context c
                EUR = 1.11 USD
                # Note that we're changing which unit GBP is defined against
                GBP = 1.18 EUR
            @end
            """.splitlines()
        )

        q = ureg.Quantity("10 GBP")
        self.assertEquals(q.magnitude, 10)
        self.assertEquals(q.units.dimensionality, {"[currency]": 1})
        self.assertEquals(q.to("GBP").magnitude, 10)
        self.assertTrue(math.isnan(q.to("USD").magnitude))
        self.assertAlmostEqual(q.to("USD", "c").magnitude, 10 * 1.18 * 1.11)

    def test_non_multiplicative(self):
        ureg = UnitRegistry(
            """
            kelvin = [temperature]
            fahrenheit = 5 / 9 * kelvin; offset: 255
            bogodegrees = 9 * kelvin

            @context nonmult_to_nonmult
                fahrenheit = 7 * kelvin; offset: 123
            @end
            @context nonmult_to_mult
                fahrenheit = 123 * kelvin
            @end
            @context mult_to_nonmult
                bogodegrees = 5 * kelvin; offset: 123
            @end
            """.splitlines()
        )
        k = ureg.Quantity(100, "kelvin")

        with self.subTest("baseline"):
            self.assertAlmostEqual(k.to("fahrenheit").magnitude, (100 - 255) * 9 / 5)
            self.assertAlmostEqual(k.to("bogodegrees").magnitude, 100 / 9)

        with self.subTest("nonmult_to_nonmult"):
            with ureg.context("nonmult_to_nonmult"):
                self.assertAlmostEqual(k.to("fahrenheit").magnitude, (100 - 123) / 7)

        with self.subTest("nonmult_to_mult"):
            with ureg.context("nonmult_to_mult"):
                self.assertAlmostEqual(k.to("fahrenheit").magnitude, 100 / 123)

        with self.subTest("mult_to_nonmult"):
            with ureg.context("mult_to_nonmult"):
                self.assertAlmostEqual(k.to("bogodegrees").magnitude, (100 - 123) / 5)

    def test_stack_contexts(self):
        ureg = UnitRegistry(
            """
            a = [dim1]
            b = 1/2 a
            c = 1/3 a
            d = [dim2]

            @context c1
                b = 1/4 a
                c = 1/6 a
                [dim1]->[dim2]: value * 2 d/a
            @end
            @context c2
                b = 1/5 a
                [dim1]->[dim2]: value * 3 d/a
            @end
            """.splitlines()
        )
        q = ureg.Quantity(1, "a")
        assert q.to("b").magnitude == 2
        assert q.to("c").magnitude == 3
        assert q.to("b", "c1").magnitude == 4
        assert q.to("c", "c1").magnitude == 6
        assert q.to("d", "c1").magnitude == 2
        assert q.to("b", "c2").magnitude == 5
        assert q.to("c", "c2").magnitude == 3
        assert q.to("d", "c2").magnitude == 3
        assert q.to("b", "c1", "c2").magnitude == 5  # c2 takes precedence
        assert q.to("c", "c1", "c2").magnitude == 6  # c2 doesn't change it, so use c1
        assert q.to("d", "c1", "c2").magnitude == 3  # c2 takes precedence

    def test_err_to_base_unit(self):
        with self.assertRaises(DefinitionSyntaxError) as e:
            Context.from_lines(["@context c", "x = [d]"])
        self.assertEquals(str(e.exception), "Can't define base units within a context")

    def test_err_change_base_unit(self):
        ureg = UnitRegistry(
            """
            foo = [d1]
            bar = [d2]

            @context c
                bar = foo
            @end
            """.splitlines()
        )

        with self.assertRaises(ValueError) as e:
            ureg.enable_contexts("c")
        self.assertEquals(
            str(e.exception), "Can't redefine a base unit to a derived one"
        )

    def test_err_change_dimensionality(self):
        ureg = UnitRegistry(
            """
            foo = [d1]
            bar = [d2]
            baz = foo

            @context c
                baz = bar
            @end
            """.splitlines()
        )
        with self.assertRaises(ValueError) as e:
            ureg.enable_contexts("c")
        self.assertEquals(
            str(e.exception),
            "Can't change dimensionality of baz from [d1] to [d2] in a context",
        )

    def test_err_cyclic_dependency(self):
        ureg = UnitRegistry(
            """
            foo = [d]
            bar = foo
            baz = bar

            @context c
                bar = baz
            @end
            """.splitlines()
        )
        # TODO align this exception and the one you get when you implement a cyclic
        #      dependency within the base registry. Ideally this exception should be
        #      raised by enable_contexts.
        ureg.enable_contexts("c")
        q = ureg.Quantity("bar")
        with self.assertRaises(RecursionError):
            q.to("foo")

    def test_err_dimension_redefinition(self):
        with self.assertRaises(DefinitionSyntaxError) as e:
            Context.from_lines(["@context c", "[d1] = [d2] * [d3]"])
        self.assertEquals(
            str(e.exception), "Expected <unit> = <converter>; got [d1] = [d2] * [d3]"
        )

    def test_err_prefix_redefinition(self):
        with self.assertRaises(DefinitionSyntaxError) as e:
            Context.from_lines(["@context c", "[d1] = [d2] * [d3]"])
        self.assertEquals(
            str(e.exception), "Expected <unit> = <converter>; got [d1] = [d2] * [d3]"
        )

    def test_err_redefine_alias(self):
        for s in ("foo = bar = f", "foo = bar = _ = baz"):
            with self.subTest(s):
                with self.assertRaises(DefinitionSyntaxError) as e:
                    Context.from_lines(["@context c", s])
                self.assertEquals(
                    str(e.exception),
                    "Can't change a unit's symbol or aliases within a context",
                )

    def test_err_redefine_with_prefix(self):
        ureg = UnitRegistry(
            """
            kilo- = 1000
            gram = [mass]
            pound = 454 gram

            @context c
                kilopound = 500000 gram
            @end
            """.splitlines()
        )
        with self.assertRaises(ValueError) as e:
            ureg.enable_contexts("c")
        self.assertEquals(
            str(e.exception), "Can't redefine a unit with a prefix: kilopound"
        )

    def test_err_new_unit(self):
        ureg = UnitRegistry(
            """
            foo = [d]
            @context c
                bar = foo
            @end
            """.splitlines()
        )
        with self.assertRaises(UndefinedUnitError) as e:
            ureg.enable_contexts("c")
        self.assertEquals(str(e.exception), "'bar' is not defined in the unit registry")
