import copy
import functools
import math
import re

from pint import (
    DefinitionSyntaxError,
    DimensionalityError,
    RedefinitionError,
    UndefinedUnitError,
)
from pint.compat import np
from pint.registry import LazyRegistry, UnitRegistry
from pint.testsuite import CaseInsensitveQuantityTestCase, QuantityTestCase, helpers
from pint.testsuite.parameterized import ParameterizedTestCase
from pint.util import ParserHelper, UnitsContainer


class TestUnit(QuantityTestCase):
    def test_creation(self):
        for arg in ("meter", UnitsContainer(meter=1), self.U_("m")):
            self.assertEqual(self.U_(arg)._units, UnitsContainer(meter=1))
        self.assertRaises(TypeError, self.U_, 1)

    def test_deepcopy(self):
        x = self.U_(UnitsContainer(meter=1))
        self.assertEqual(x, copy.deepcopy(x))

    def test_unit_repr(self):
        x = self.U_(UnitsContainer(meter=1))
        self.assertEqual(str(x), "meter")
        self.assertEqual(repr(x), "<Unit('meter')>")

    def test_unit_formatting(self):
        x = self.U_(UnitsContainer(meter=2, kilogram=1, second=-1))
        for spec, result in (
            ("{}", str(x)),
            ("{!s}", str(x)),
            ("{!r}", repr(x)),
            (
                "{:L}",
                r"\frac{\mathrm{kilogram} \cdot \mathrm{meter}^{2}}{\mathrm{second}}",
            ),
            ("{:P}", "kilogram·meter²/second"),
            ("{:H}", "kilogram meter<sup>2</sup>/second"),
            ("{:C}", "kilogram*meter**2/second"),
            ("{:Lx}", r"\si[]{\kilo\gram\meter\squared\per\second}"),
            ("{:~}", "kg * m ** 2 / s"),
            ("{:L~}", r"\frac{\mathrm{kg} \cdot \mathrm{m}^{2}}{\mathrm{s}}"),
            ("{:P~}", "kg·m²/s"),
            ("{:H~}", "kg m<sup>2</sup>/s"),
            ("{:C~}", "kg*m**2/s"),
        ):
            with self.subTest(spec):
                self.assertEqual(spec.format(x), result)

    def test_unit_default_formatting(self):
        ureg = UnitRegistry()
        x = ureg.Unit(UnitsContainer(meter=2, kilogram=1, second=-1))
        for spec, result in (
            (
                "L",
                r"\frac{\mathrm{kilogram} \cdot \mathrm{meter}^{2}}{\mathrm{second}}",
            ),
            ("P", "kilogram·meter²/second"),
            ("H", "kilogram meter<sup>2</sup>/second"),
            ("C", "kilogram*meter**2/second"),
            ("~", "kg * m ** 2 / s"),
            ("L~", r"\frac{\mathrm{kg} \cdot \mathrm{m}^{2}}{\mathrm{s}}"),
            ("P~", "kg·m²/s"),
            ("H~", "kg m<sup>2</sup>/s"),
            ("C~", "kg*m**2/s"),
        ):
            with self.subTest(spec):
                ureg.default_format = spec
                self.assertEqual(f"{x}", result, f"Failed for {spec}, {result}")

    def test_unit_formatting_snake_case(self):
        # Test that snake_case units are escaped where appropriate
        ureg = UnitRegistry()
        x = ureg.Unit(UnitsContainer(oil_barrel=1))
        for spec, result in (
            ("L", r"\mathrm{oil\_barrel}"),
            ("P", "oil_barrel"),
            ("H", "oil_barrel"),
            ("C", "oil_barrel"),
            ("~", "oil_bbl"),
            ("L~", r"\mathrm{oil\_bbl}"),
            ("P~", "oil_bbl"),
            ("H~", "oil_bbl"),
            ("C~", "oil_bbl"),
        ):
            with self.subTest(spec):
                ureg.default_format = spec
                self.assertEqual(f"{x}", result, f"Failed for {spec}, {result}")

    def test_ipython(self):
        alltext = []

        class Pretty:
            @staticmethod
            def text(text):
                alltext.append(text)

        ureg = UnitRegistry()
        x = ureg.Unit(UnitsContainer(meter=2, kilogram=1, second=-1))
        self.assertEqual(x._repr_html_(), "kilogram meter<sup>2</sup>/second")
        self.assertEqual(
            x._repr_latex_(),
            r"$\frac{\mathrm{kilogram} \cdot " r"\mathrm{meter}^{2}}{\mathrm{second}}$",
        )
        x._repr_pretty_(Pretty, False)
        self.assertEqual("".join(alltext), "kilogram·meter²/second")
        ureg.default_format = "~"
        self.assertEqual(x._repr_html_(), "kg m<sup>2</sup>/s")
        self.assertEqual(
            x._repr_latex_(), r"$\frac{\mathrm{kg} \cdot \mathrm{m}^{2}}{\mathrm{s}}$"
        )
        alltext = []
        x._repr_pretty_(Pretty, False)
        self.assertEqual("".join(alltext), "kg·m²/s")

    def test_unit_mul(self):
        x = self.U_("m")
        self.assertEqual(x * 1, self.Q_(1, "m"))
        self.assertEqual(x * 0.5, self.Q_(0.5, "m"))
        self.assertEqual(x * self.Q_(1, "m"), self.Q_(1, "m**2"))
        self.assertEqual(1 * x, self.Q_(1, "m"))

    def test_unit_div(self):
        x = self.U_("m")
        self.assertEqual(x / 1, self.Q_(1, "m"))
        self.assertEqual(x / 0.5, self.Q_(2.0, "m"))
        self.assertEqual(x / self.Q_(1, "m"), self.Q_(1))

    def test_unit_rdiv(self):
        x = self.U_("m")
        self.assertEqual(1 / x, self.Q_(1, "1/m"))

    def test_unit_pow(self):
        x = self.U_("m")
        self.assertEqual(x ** 2, self.U_("m**2"))

    def test_unit_hash(self):
        x = self.U_("m")
        self.assertEqual(hash(x), hash(x._units))

    def test_unit_eqs(self):
        x = self.U_("m")
        self.assertEqual(x, self.U_("m"))
        self.assertNotEqual(x, self.U_("cm"))

        self.assertEqual(x, self.Q_(1, "m"))
        self.assertNotEqual(x, self.Q_(2, "m"))

        self.assertEqual(x, UnitsContainer({"meter": 1}))

        y = self.U_("cm/m")
        self.assertEqual(y, 0.01)

        self.assertEqual(self.U_("byte") == self.U_("byte"), True)
        self.assertEqual(self.U_("byte") != self.U_("byte"), False)

    def test_unit_cmp(self):

        x = self.U_("m")
        self.assertLess(x, self.U_("km"))
        self.assertGreater(x, self.U_("mm"))

        y = self.U_("m/mm")
        self.assertGreater(y, 1)
        self.assertLess(y, 1e6)

    def test_dimensionality(self):

        x = self.U_("m")
        self.assertEqual(x.dimensionality, UnitsContainer({"[length]": 1}))

    def test_dimensionless(self):

        self.assertTrue(self.U_("m/mm").dimensionless)
        self.assertFalse(self.U_("m").dimensionless)

    def test_unit_casting(self):

        self.assertEqual(int(self.U_("m/mm")), 1000)
        self.assertEqual(float(self.U_("mm/m")), 1e-3)
        self.assertEqual(complex(self.U_("mm/mm")), 1 + 0j)

    @helpers.requires_numpy()
    def test_array_interface(self):
        import numpy as np

        x = self.U_("m")
        arr = np.ones(10)
        self.assertQuantityEqual(arr * x, self.Q_(arr, "m"))
        self.assertQuantityEqual(arr / x, self.Q_(arr, "1/m"))
        self.assertQuantityEqual(x / arr, self.Q_(arr, "m"))


class TestRegistry(QuantityTestCase):

    FORCE_NDARRAY = False

    def setup(self):
        self.ureg.autoconvert_offset_to_baseunit = False

    def test_base(self):
        ureg = UnitRegistry(None)
        ureg.define("meter = [length]")
        self.assertRaises(DefinitionSyntaxError, ureg.define, "meter = [length]")
        self.assertRaises(TypeError, ureg.define, list())
        ureg.define("degC = kelvin; offset: 273.15")

    def test_define(self):
        ureg = UnitRegistry(None)
        self.assertIsInstance(dir(ureg), list)
        self.assertGreater(len(dir(ureg)), 0)

    def test_load(self):
        import pkg_resources

        from pint import unit

        data = pkg_resources.resource_filename(unit.__name__, "default_en.txt")
        ureg1 = UnitRegistry()
        ureg2 = UnitRegistry(data)
        self.assertEqual(dir(ureg1), dir(ureg2))
        self.assertRaises(
            ValueError, UnitRegistry(None).load_definitions, "notexisting"
        )

    def test_default_format(self):
        ureg = UnitRegistry()
        q = ureg.meter
        s1 = f"{q}"
        s2 = f"{q:~}"
        ureg.default_format = "~"
        s3 = f"{q}"
        self.assertEqual(s2, s3)
        self.assertNotEqual(s1, s3)
        self.assertEqual(ureg.default_format, "~")

    def test_iterate(self):
        ureg = UnitRegistry()
        self.assertTrue("meter" in list(ureg))

    def test_parse_number(self):
        self.assertEqual(self.ureg.parse_expression("pi"), math.pi)
        self.assertEqual(self.ureg.parse_expression("x", x=2), 2)
        self.assertEqual(self.ureg.parse_expression("x", x=2.3), 2.3)
        self.assertEqual(self.ureg.parse_expression("x * y", x=2.3, y=3), 2.3 * 3)
        self.assertEqual(self.ureg.parse_expression("x", x=(1 + 1j)), (1 + 1j))

    def test_parse_single(self):
        self.assertEqual(
            self.ureg.parse_expression("meter"), self.Q_(1, UnitsContainer(meter=1.0))
        )
        self.assertEqual(
            self.ureg.parse_expression("second"), self.Q_(1, UnitsContainer(second=1.0))
        )

    def test_parse_alias(self):
        self.assertEqual(
            self.ureg.parse_expression("metre"), self.Q_(1, UnitsContainer(meter=1.0))
        )

    def test_parse_plural(self):
        self.assertEqual(
            self.ureg.parse_expression("meters"), self.Q_(1, UnitsContainer(meter=1.0))
        )

    def test_parse_prefix(self):
        self.assertEqual(
            self.ureg.parse_expression("kilometer"),
            self.Q_(1, UnitsContainer(kilometer=1.0)),
        )

    def test_parse_complex(self):
        self.assertEqual(
            self.ureg.parse_expression("kilometre"),
            self.Q_(1, UnitsContainer(kilometer=1.0)),
        )
        self.assertEqual(
            self.ureg.parse_expression("kilometres"),
            self.Q_(1, UnitsContainer(kilometer=1.0)),
        )

    def test_parse_mul_div(self):
        self.assertEqual(
            self.ureg.parse_expression("meter*meter"),
            self.Q_(1, UnitsContainer(meter=2.0)),
        )
        self.assertEqual(
            self.ureg.parse_expression("meter**2"),
            self.Q_(1, UnitsContainer(meter=2.0)),
        )
        self.assertEqual(
            self.ureg.parse_expression("meter*second"),
            self.Q_(1, UnitsContainer(meter=1.0, second=1)),
        )
        self.assertEqual(
            self.ureg.parse_expression("meter/second"),
            self.Q_(1, UnitsContainer(meter=1.0, second=-1)),
        )
        self.assertEqual(
            self.ureg.parse_expression("meter/second**2"),
            self.Q_(1, UnitsContainer(meter=1.0, second=-2)),
        )

    def test_parse_pretty(self):
        self.assertEqual(
            self.ureg.parse_expression("meter/second²"),
            self.Q_(1, UnitsContainer(meter=1.0, second=-2)),
        )
        self.assertEqual(
            self.ureg.parse_expression("m³/s³"),
            self.Q_(1, UnitsContainer(meter=3.0, second=-3)),
        )
        self.assertEqual(
            self.ureg.parse_expression("meter² · second"),
            self.Q_(1, UnitsContainer(meter=2.0, second=1)),
        )
        self.assertEqual(
            self.ureg.parse_expression("meter⁰.⁵·second"),
            self.Q_(1, UnitsContainer(meter=0.5, second=1)),
        )
        self.assertEqual(
            self.ureg.parse_expression("meter³⁷/second⁴.³²¹"),
            self.Q_(1, UnitsContainer(meter=37, second=-4.321)),
        )

    def test_parse_factor(self):
        self.assertEqual(
            self.ureg.parse_expression("42*meter"),
            self.Q_(42, UnitsContainer(meter=1.0)),
        )
        self.assertEqual(
            self.ureg.parse_expression("meter*42"),
            self.Q_(42, UnitsContainer(meter=1.0)),
        )

    def test_rep_and_parse(self):
        q = self.Q_(1, "g/(m**2*s)")
        self.assertEqual(self.Q_(q.magnitude, str(q.units)), q)

    def test_as_delta(self):
        parse = self.ureg.parse_units
        self.assertEqual(parse("kelvin", as_delta=True), UnitsContainer(kelvin=1))
        self.assertEqual(parse("kelvin", as_delta=False), UnitsContainer(kelvin=1))
        self.assertEqual(
            parse("kelvin**(-1)", as_delta=True), UnitsContainer(kelvin=-1)
        )
        self.assertEqual(
            parse("kelvin**(-1)", as_delta=False), UnitsContainer(kelvin=-1)
        )
        self.assertEqual(parse("kelvin**2", as_delta=True), UnitsContainer(kelvin=2))
        self.assertEqual(parse("kelvin**2", as_delta=False), UnitsContainer(kelvin=2))
        self.assertEqual(
            parse("kelvin*meter", as_delta=True), UnitsContainer(kelvin=1, meter=1)
        )
        self.assertEqual(
            parse("kelvin*meter", as_delta=False), UnitsContainer(kelvin=1, meter=1)
        )

    def test_parse_expression_with_preprocessor(self):
        # Add parsing of UDUNITS-style power
        self.ureg.preprocessors.append(
            functools.partial(
                re.sub,
                r"(?<=[A-Za-z])(?![A-Za-z])(?<![0-9\-][eE])(?<![0-9\-])(?=[0-9\-])",
                "**",
            )
        )
        # Test equality
        self.assertEqual(
            self.ureg.parse_expression("42 m2"), self.Q_(42, UnitsContainer(meter=2.0))
        )
        self.assertEqual(
            self.ureg.parse_expression("1e6 Hz s-2"),
            self.Q_(1e6, UnitsContainer(second=-3.0)),
        )
        self.assertEqual(
            self.ureg.parse_expression("3 metre3"),
            self.Q_(3, UnitsContainer(meter=3.0)),
        )
        # Clean up and test previously expected value
        self.ureg.preprocessors.pop()
        self.assertEqual(
            self.ureg.parse_expression("1e6 Hz s-2"),
            self.Q_(999998.0, UnitsContainer()),
        )

    def test_parse_unit_with_preprocessor(self):
        # Add parsing of UDUNITS-style power
        self.ureg.preprocessors.append(
            functools.partial(
                re.sub,
                r"(?<=[A-Za-z])(?![A-Za-z])(?<![0-9\-][eE])(?<![0-9\-])(?=[0-9\-])",
                "**",
            )
        )
        # Test equality
        self.assertEqual(self.ureg.parse_units("m2"), UnitsContainer(meter=2.0))
        self.assertEqual(self.ureg.parse_units("m-2"), UnitsContainer(meter=-2.0))
        # Clean up
        self.ureg.preprocessors.pop()

    def test_name(self):
        self.assertRaises(UndefinedUnitError, self.ureg.get_name, "asdf")

    def test_symbol(self):
        self.assertRaises(UndefinedUnitError, self.ureg.get_symbol, "asdf")

        self.assertEqual(self.ureg.get_symbol("meter"), "m")
        self.assertEqual(self.ureg.get_symbol("second"), "s")
        self.assertEqual(self.ureg.get_symbol("hertz"), "Hz")

        self.assertEqual(self.ureg.get_symbol("kilometer"), "km")
        self.assertEqual(self.ureg.get_symbol("megahertz"), "MHz")
        self.assertEqual(self.ureg.get_symbol("millisecond"), "ms")

    def test_imperial_symbol(self):
        self.assertEqual(self.ureg.get_symbol("inch"), "in")
        self.assertEqual(self.ureg.get_symbol("foot"), "ft")
        self.assertEqual(self.ureg.get_symbol("inches"), "in")
        self.assertEqual(self.ureg.get_symbol("feet"), "ft")
        self.assertEqual(self.ureg.get_symbol("international_foot"), "ft")
        self.assertEqual(self.ureg.get_symbol("international_inch"), "in")

    def test_pint(self):
        self.assertLess(self.ureg.pint, self.ureg.liter)
        self.assertLess(self.ureg.pint, self.ureg.imperial_pint)

    def test_wraps(self):
        def func(x):
            return x

        ureg = self.ureg

        self.assertRaises(TypeError, ureg.wraps, (3 * ureg.meter, [None]))
        self.assertRaises(TypeError, ureg.wraps, (None, [3 * ureg.meter]))

        f0 = ureg.wraps(None, [None])(func)
        self.assertEqual(f0(3.0), 3.0)

        f0 = ureg.wraps(None, None)(func)
        self.assertEqual(f0(3.0), 3.0)

        f1 = ureg.wraps(None, ["meter"])(func)
        self.assertRaises(ValueError, f1, 3.0)
        self.assertEqual(f1(3.0 * ureg.centimeter), 0.03)
        self.assertEqual(f1(3.0 * ureg.meter), 3.0)
        self.assertRaises(DimensionalityError, f1, 3 * ureg.second)

        f1b = ureg.wraps(None, [ureg.meter])(func)
        self.assertRaises(ValueError, f1b, 3.0)
        self.assertEqual(f1b(3.0 * ureg.centimeter), 0.03)
        self.assertEqual(f1b(3.0 * ureg.meter), 3.0)
        self.assertRaises(DimensionalityError, f1b, 3 * ureg.second)

        f1c = ureg.wraps("meter", [ureg.meter])(func)
        self.assertEqual(f1c(3.0 * ureg.centimeter), 0.03 * ureg.meter)
        self.assertEqual(f1c(3.0 * ureg.meter), 3.0 * ureg.meter)
        self.assertRaises(DimensionalityError, f1c, 3 * ureg.second)

        f1d = ureg.wraps(ureg.meter, [ureg.meter])(func)
        self.assertEqual(f1d(3.0 * ureg.centimeter), 0.03 * ureg.meter)
        self.assertEqual(f1d(3.0 * ureg.meter), 3.0 * ureg.meter)
        self.assertRaises(DimensionalityError, f1d, 3 * ureg.second)

        f1 = ureg.wraps(None, "meter")(func)
        self.assertRaises(ValueError, f1, 3.0)
        self.assertEqual(f1(3.0 * ureg.centimeter), 0.03)
        self.assertEqual(f1(3.0 * ureg.meter), 3.0)
        self.assertRaises(DimensionalityError, f1, 3 * ureg.second)

        f2 = ureg.wraps("centimeter", ["meter"])(func)
        self.assertRaises(ValueError, f2, 3.0)
        self.assertEqual(f2(3.0 * ureg.centimeter), 0.03 * ureg.centimeter)
        self.assertEqual(f2(3.0 * ureg.meter), 3 * ureg.centimeter)

        f3 = ureg.wraps("centimeter", ["meter"], strict=False)(func)
        self.assertEqual(f3(3), 3 * ureg.centimeter)
        self.assertEqual(f3(3.0 * ureg.centimeter), 0.03 * ureg.centimeter)
        self.assertEqual(f3(3.0 * ureg.meter), 3.0 * ureg.centimeter)

        def gfunc(x, y):
            return x + y

        g0 = ureg.wraps(None, [None, None])(gfunc)
        self.assertEqual(g0(3, 1), 4)

        g1 = ureg.wraps(None, ["meter", "centimeter"])(gfunc)
        self.assertRaises(ValueError, g1, 3 * ureg.meter, 1)
        self.assertEqual(g1(3 * ureg.meter, 1 * ureg.centimeter), 4)
        self.assertEqual(g1(3 * ureg.meter, 1 * ureg.meter), 3 + 100)

        def hfunc(x, y):
            return x, y

        h0 = ureg.wraps(None, [None, None])(hfunc)
        self.assertEqual(h0(3, 1), (3, 1))

        h1 = ureg.wraps(["meter", "centimeter"], [None, None])(hfunc)
        self.assertEqual(h1(3, 1), [3 * ureg.meter, 1 * ureg.cm])

        h2 = ureg.wraps(("meter", "centimeter"), [None, None])(hfunc)
        self.assertEqual(h2(3, 1), (3 * ureg.meter, 1 * ureg.cm))

        h3 = ureg.wraps((None,), (None, None))(hfunc)
        self.assertEqual(h3(3, 1), (3, 1))

    def test_wrap_referencing(self):

        ureg = self.ureg

        def gfunc(x, y):
            return x + y

        def gfunc2(x, y):
            return x ** 2 + y

        def gfunc3(x, y):
            return x ** 2 * y

        rst = 3.0 * ureg.meter + 1.0 * ureg.centimeter

        g0 = ureg.wraps("=A", ["=A", "=A"])(gfunc)
        self.assertEqual(g0(3.0 * ureg.meter, 1.0 * ureg.centimeter), rst.to("meter"))
        self.assertEqual(g0(3, 1), 4)

        g1 = ureg.wraps("=A", ["=A", "=A"])(gfunc)
        self.assertEqual(
            g1(3.0 * ureg.meter, 1.0 * ureg.centimeter), rst.to("centimeter")
        )

        g2 = ureg.wraps("=A", ["=A", "=A"])(gfunc)
        self.assertEqual(g2(3.0 * ureg.meter, 1.0 * ureg.centimeter), rst.to("meter"))

        g3 = ureg.wraps("=A**2", ["=A", "=A**2"])(gfunc2)
        a = 3.0 * ureg.meter
        b = (2.0 * ureg.centimeter) ** 2
        self.assertEqual(g3(a, b), gfunc2(a, b))
        self.assertEqual(g3(3, 2), gfunc2(3, 2))

        g4 = ureg.wraps("=A**2 * B", ["=A", "=B"])(gfunc3)
        self.assertEqual(
            g4(3.0 * ureg.meter, 2.0 * ureg.second), ureg("(3*meter)**2 * 2 *second")
        )
        self.assertEqual(g4(3.0 * ureg.meter, 2.0), ureg("(3*meter)**2 * 2"))
        self.assertEqual(g4(3.0, 2.0 * ureg.second), ureg("3**2 * 2 * second"))

    def test_check(self):
        def func(x):
            return x

        ureg = self.ureg

        f0 = ureg.check("[length]")(func)
        self.assertRaises(DimensionalityError, f0, 3.0)
        self.assertEqual(f0(3.0 * ureg.centimeter), 0.03 * ureg.meter)
        self.assertRaises(DimensionalityError, f0, 3.0 * ureg.kilogram)

        f0b = ureg.check(ureg.meter)(func)
        self.assertRaises(DimensionalityError, f0b, 3.0)
        self.assertEqual(f0b(3.0 * ureg.centimeter), 0.03 * ureg.meter)
        self.assertRaises(DimensionalityError, f0b, 3.0 * ureg.kilogram)

        def gfunc(x, y):
            return x / y

        g0 = ureg.check(None, None)(gfunc)
        self.assertEqual(g0(6, 2), 3)
        self.assertEqual(g0(6 * ureg.parsec, 2), 3 * ureg.parsec)

        g1 = ureg.check("[speed]", "[time]")(gfunc)
        self.assertRaises(DimensionalityError, g1, 3.0, 1)
        self.assertRaises(DimensionalityError, g1, 1 * ureg.parsec, 1 * ureg.angstrom)
        self.assertRaises(TypeError, g1, 1 * ureg.km / ureg.hour, 1 * ureg.hour, 3.0)
        self.assertEqual(
            g1(3.6 * ureg.km / ureg.hour, 1 * ureg.second),
            1 * ureg.meter / ureg.second ** 2,
        )

        self.assertRaises(TypeError, ureg.check("[speed]"), gfunc)
        self.assertRaises(TypeError, ureg.check("[speed]", "[time]", "[mass]"), gfunc)

    def test_to_ref_vs_to(self):
        self.ureg.autoconvert_offset_to_baseunit = True
        q = 8.0 * self.ureg.inch
        t = 8.0 * self.ureg.degF
        dt = 8.0 * self.ureg.delta_degF
        self.assertEqual(
            q.to("yard").magnitude, self.ureg._units["inch"].converter.to_reference(8.0)
        )
        self.assertEqual(
            t.to("kelvin").magnitude,
            self.ureg._units["degF"].converter.to_reference(8.0),
        )
        self.assertEqual(
            dt.to("kelvin").magnitude,
            self.ureg._units["delta_degF"].converter.to_reference(8.0),
        )

    def test_redefinition(self):
        d = UnitRegistry().define

        with self.capture_log() as buffer:
            d("meter = [fruits]")
            d("kilo- = 1000")
            d("[speed] = [vegetables]")

            # aliases
            d("bla = 3.2 meter = inch")
            d("myk- = 1000 = kilo-")

            self.assertEqual(len(buffer), 5)

    def test_convert_parse_str(self):
        ureg = self.ureg
        self.assertEqual(
            ureg.convert(1, "meter", "inch"),
            ureg.convert(1, UnitsContainer(meter=1), UnitsContainer(inch=1)),
        )

    @helpers.requires_numpy()
    def test_convert_inplace(self):
        ureg = self.ureg

        # Conversions with single units take a different codepath than
        # Conversions with more than one unit.
        src_dst1 = UnitsContainer(meter=1), UnitsContainer(inch=1)
        src_dst2 = UnitsContainer(meter=1, second=-1), UnitsContainer(inch=1, minute=-1)
        for src, dst in (src_dst1, src_dst2):
            v = (ureg.convert(1, src, dst),)

            a = np.ones((3, 1))
            ac = np.ones((3, 1))

            r1 = ureg.convert(a, src, dst)
            np.testing.assert_allclose(r1, v * ac)
            self.assertIsNot(r1, a)

            r2 = ureg.convert(a, src, dst, inplace=True)
            np.testing.assert_allclose(r2, v * ac)
            self.assertIs(r2, a)

    def test_repeated_convert(self):
        # Because of caching, repeated conversions were failing.
        self.ureg.convert(1, "m", "ft")
        self.ureg.convert(1, "m", "ft")

    def test_singular_SI_prefix_convert(self):
        # Fix for issue 156
        self.ureg.convert(1, "mm", "m")
        self.ureg.convert(1, "ms", "s")
        self.ureg.convert(1, "m", "mm")
        self.ureg.convert(1, "s", "ms")

    def test_parse_units(self):
        ureg = self.ureg
        self.assertEqual(ureg.parse_units(""), ureg.Unit(""))
        self.assertRaises(ValueError, ureg.parse_units, "2 * meter")

    def test_parse_string_pattern(self):
        ureg = self.ureg
        self.assertEqual(
            ureg.parse_pattern("10'11", r"{foot}'{inch}"),
            [ureg.Quantity(10.0, "foot"), ureg.Quantity(11.0, "inch")],
        )

    def test_parse_string_pattern_no_preprocess(self):
        """Were preprocessors enabled, this would be interpreted as 10*11, not
        two separate units, and thus cause the parsing to fail"""
        ureg = self.ureg
        self.assertEqual(
            ureg.parse_pattern("10 11", r"{kg} {lb}"),
            [ureg.Quantity(10.0, "kilogram"), ureg.Quantity(11.0, "pound")],
        )

    def test_parse_pattern_many_results(self):
        ureg = self.ureg
        self.assertEqual(
            ureg.parse_pattern(
                "1.5kg or 2kg will be fine, if you do not have 3kg",
                r"{kg}kg",
                many=True,
            ),
            [
                [ureg.Quantity(1.5, "kilogram")],
                [ureg.Quantity(2.0, "kilogram")],
                [ureg.Quantity(3.0, "kilogram")],
            ],
        )

    def test_parse_pattern_many_results_two_units(self):
        ureg = self.ureg
        self.assertEqual(
            ureg.parse_pattern("10'10 or 10'11", "{foot}'{inch}", many=True),
            [
                [ureg.Quantity(10.0, "foot"), ureg.Quantity(10.0, "inch")],
                [ureg.Quantity(10.0, "foot"), ureg.Quantity(11.0, "inch")],
            ],
        )

    def test_case_sensitivity(self):
        ureg = self.ureg
        # Default
        self.assertRaises(UndefinedUnitError, ureg.parse_units, "Meter")
        self.assertRaises(UndefinedUnitError, ureg.parse_units, "j")
        # Force True
        self.assertRaises(
            UndefinedUnitError, ureg.parse_units, "Meter", case_sensitive=True
        )
        self.assertRaises(
            UndefinedUnitError, ureg.parse_units, "j", case_sensitive=True
        )
        # Force False
        self.assertEqual(
            ureg.parse_units("Meter", case_sensitive=False), UnitsContainer(meter=1)
        )
        self.assertEqual(
            ureg.parse_units("j", case_sensitive=False), UnitsContainer(joule=1)
        )


class TestCaseInsensitiveRegistry(CaseInsensitveQuantityTestCase):
    def test_case_sensitivity(self):
        ureg = self.ureg
        # Default
        self.assertEqual(ureg.parse_units("Meter"), UnitsContainer(meter=1))
        self.assertEqual(ureg.parse_units("j"), UnitsContainer(joule=1))
        # Force True
        self.assertRaises(
            UndefinedUnitError, ureg.parse_units, "Meter", case_sensitive=True
        )
        self.assertRaises(
            UndefinedUnitError, ureg.parse_units, "j", case_sensitive=True
        )
        # Force False
        self.assertEqual(
            ureg.parse_units("Meter", case_sensitive=False), UnitsContainer(meter=1)
        )
        self.assertEqual(
            ureg.parse_units("j", case_sensitive=False), UnitsContainer(joule=1)
        )


class TestCompatibleUnits(QuantityTestCase):
    FORCE_NDARRAY = False

    def setUp(self):
        super().setUp()
        self.ureg = UnitRegistry(force_ndarray=self.FORCE_NDARRAY)
        self.Q_ = self.ureg.Quantity
        self.U_ = self.ureg.Unit

    def _test(self, input_units):
        gd = self.ureg.get_dimensionality
        dim = gd(input_units)
        equiv = self.ureg.get_compatible_units(input_units)
        for eq in equiv:
            self.assertEqual(gd(eq), dim)
        self.assertEqual(equiv, self.ureg.get_compatible_units(dim))

    def _test2(self, units1, units2):
        equiv1 = self.ureg.get_compatible_units(units1)
        equiv2 = self.ureg.get_compatible_units(units2)
        self.assertEqual(equiv1, equiv2)

    def test_many(self):
        self._test(self.ureg.meter)
        self._test(self.ureg.seconds)
        self._test(self.ureg.newton)
        self._test(self.ureg.kelvin)

    def test_context_sp(self):

        gd = self.ureg.get_dimensionality

        # length, frequency, energy
        valid = [
            gd(self.ureg.meter),
            gd(self.ureg.hertz),
            gd(self.ureg.joule),
            1 / gd(self.ureg.meter),
        ]

        with self.ureg.context("sp"):
            equiv = self.ureg.get_compatible_units(self.ureg.meter)
            result = set()
            for eq in equiv:
                dim = gd(eq)
                result.add(dim)
                self.assertIn(dim, valid)

            self.assertEqual(len(result), len(valid))

    def test_get_base_units(self):
        ureg = UnitRegistry()
        self.assertEqual(ureg.get_base_units(""), (1, ureg.Unit("")))
        self.assertEqual(ureg.get_base_units("pi"), (math.pi, ureg.Unit("")))
        self.assertEqual(ureg.get_base_units("ln10"), (math.log(10), ureg.Unit("")))
        self.assertEqual(
            ureg.get_base_units("meter"), ureg.get_base_units(ParserHelper(meter=1))
        )

    def test_get_compatible_units(self):
        ureg = UnitRegistry()
        self.assertEqual(ureg.get_compatible_units(""), frozenset())
        self.assertEqual(
            ureg.get_compatible_units("meter"),
            ureg.get_compatible_units(ParserHelper(meter=1)),
        )


class TestRegistryWithDefaultRegistry(TestRegistry):
    @classmethod
    def setUpClass(cls):
        from pint import _DEFAULT_REGISTRY

        cls.ureg = _DEFAULT_REGISTRY
        cls.Q_ = cls.ureg.Quantity

    def test_lazy(self):
        x = LazyRegistry()
        x.test = "test"
        self.assertIsInstance(x, UnitRegistry)
        y = LazyRegistry()
        y("meter")
        self.assertIsInstance(y, UnitRegistry)

    def test_redefinition(self):
        d = self.ureg.define
        self.assertRaises(DefinitionSyntaxError, d, "meter = [time]")
        self.assertRaises(RedefinitionError, d, "meter = [newdim]")
        self.assertRaises(RedefinitionError, d, "kilo- = 1000")
        self.assertRaises(RedefinitionError, d, "[speed] = [length]")

        # aliases
        self.assertIn("inch", self.ureg._units)
        self.assertRaises(RedefinitionError, d, "bla = 3.2 meter = inch")
        self.assertRaises(RedefinitionError, d, "myk- = 1000 = kilo-")


class TestConvertWithOffset(QuantityTestCase, ParameterizedTestCase):

    # The dicts in convert_with_offset are used to create a UnitsContainer.
    # We create UnitsContainer to avoid any auto-conversion of units.
    convert_with_offset = [
        (({"degC": 1}, {"degC": 1}), 10),
        (({"degC": 1}, {"kelvin": 1}), 283.15),
        (({"degC": 1}, {"degC": 1, "millimeter": 1, "meter": -1}), "error"),
        (({"degC": 1}, {"kelvin": 1, "millimeter": 1, "meter": -1}), 283150),
        (({"kelvin": 1}, {"degC": 1}), -263.15),
        (({"kelvin": 1}, {"kelvin": 1}), 10),
        (({"kelvin": 1}, {"degC": 1, "millimeter": 1, "meter": -1}), "error"),
        (({"kelvin": 1}, {"kelvin": 1, "millimeter": 1, "meter": -1}), 10000),
        (({"degC": 1, "millimeter": 1, "meter": -1}, {"degC": 1}), "error"),
        (({"degC": 1, "millimeter": 1, "meter": -1}, {"kelvin": 1}), "error"),
        (
            (
                {"degC": 1, "millimeter": 1, "meter": -1},
                {"degC": 1, "millimeter": 1, "meter": -1},
            ),
            10,
        ),
        (
            (
                {"degC": 1, "millimeter": 1, "meter": -1},
                {"kelvin": 1, "millimeter": 1, "meter": -1},
            ),
            "error",
        ),
        (({"kelvin": 1, "millimeter": 1, "meter": -1}, {"degC": 1}), -273.14),
        (({"kelvin": 1, "millimeter": 1, "meter": -1}, {"kelvin": 1}), 0.01),
        (
            (
                {"kelvin": 1, "millimeter": 1, "meter": -1},
                {"degC": 1, "millimeter": 1, "meter": -1},
            ),
            "error",
        ),
        (
            (
                {"kelvin": 1, "millimeter": 1, "meter": -1},
                {"kelvin": 1, "millimeter": 1, "meter": -1},
            ),
            10,
        ),
        (({"degC": 2}, {"kelvin": 2}), "error"),
        (({"degC": 1, "degF": 1}, {"kelvin": 2}), "error"),
        (({"degC": 1, "kelvin": 1}, {"kelvin": 2}), "error"),
    ]

    @ParameterizedTestCase.parameterize(
        ("input", "expected_output"), convert_with_offset
    )
    def test_to_and_from_offset_units(self, input_tuple, expected):
        src, dst = input_tuple
        src, dst = UnitsContainer(src), UnitsContainer(dst)
        value = 10.0
        convert = self.ureg.convert
        if isinstance(expected, str):
            self.assertRaises(DimensionalityError, convert, value, src, dst)
            if src != dst:
                self.assertRaises(DimensionalityError, convert, value, dst, src)
        else:
            self.assertQuantityAlmostEqual(
                convert(value, src, dst), expected, atol=0.001
            )
            if src != dst:
                self.assertQuantityAlmostEqual(
                    convert(expected, dst, src), value, atol=0.001
                )

    def test_alias(self):
        # Use load_definitions
        ureg = UnitRegistry(
            [
                "canonical = [] = can = alias1 = alias2\n",
                # overlapping aliases
                "@alias canonical = alias2 = alias3\n",
                # Against another alias
                "@alias alias3 = alias4\n",
            ]
        )

        # Use define
        ureg.define("@alias canonical = alias5")

        # Test that new aliases work
        # Test that pre-existing aliases and symbol are not eliminated
        for a in ("can", "alias1", "alias2", "alias3", "alias4", "alias5"):
            self.assertEqual(ureg.Unit(a), ureg.Unit("canonical"))

        # Test that aliases defined multiple times are not duplicated
        self.assertEqual(
            ureg._units["canonical"].aliases,
            ("alias1", "alias2", "alias3", "alias4", "alias5"),
        )

        # Define against unknown name
        self.assertRaises(KeyError, ureg.define, "@alias notexist = something")
