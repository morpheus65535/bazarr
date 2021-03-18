import copy
import datetime
import math
import operator as op
import pickle
import warnings
from unittest.mock import patch

from pint import DimensionalityError, OffsetUnitCalculusError, UnitRegistry
from pint.compat import np
from pint.testsuite import QuantityTestCase, helpers
from pint.testsuite.parameterized import ParameterizedTestCase
from pint.unit import UnitsContainer


class FakeWrapper:
    # Used in test_upcast_type_rejection_on_creation
    def __init__(self, q):
        self.q = q


class TestQuantity(QuantityTestCase):

    FORCE_NDARRAY = False

    def test_quantity_creation(self):
        for args in (
            (4.2, "meter"),
            (4.2, UnitsContainer(meter=1)),
            (4.2, self.ureg.meter),
            ("4.2*meter",),
            ("4.2/meter**(-1)",),
            (self.Q_(4.2, "meter"),),
        ):
            x = self.Q_(*args)
            self.assertEqual(x.magnitude, 4.2)
            self.assertEqual(x.units, UnitsContainer(meter=1))

        x = self.Q_(4.2, UnitsContainer(length=1))
        y = self.Q_(x)
        self.assertEqual(x.magnitude, y.magnitude)
        self.assertEqual(x.units, y.units)
        self.assertIsNot(x, y)

        x = self.Q_(4.2, None)
        self.assertEqual(x.magnitude, 4.2)
        self.assertEqual(x.units, UnitsContainer())

        with self.capture_log() as buffer:
            self.assertEqual(4.2 * self.ureg.meter, self.Q_(4.2, 2 * self.ureg.meter))
            self.assertEqual(len(buffer), 1)

    def test_quantity_bool(self):
        self.assertTrue(self.Q_(1, None))
        self.assertTrue(self.Q_(1, "meter"))
        self.assertFalse(self.Q_(0, None))
        self.assertFalse(self.Q_(0, "meter"))
        self.assertRaises(ValueError, bool, self.Q_(0, "degC"))
        self.assertFalse(self.Q_(0, "delta_degC"))

    def test_quantity_comparison(self):
        x = self.Q_(4.2, "meter")
        y = self.Q_(4.2, "meter")
        z = self.Q_(5, "meter")
        j = self.Q_(5, "meter*meter")

        # identity for single object
        self.assertTrue(x == x)
        self.assertFalse(x != x)

        # identity for multiple objects with same value
        self.assertTrue(x == y)
        self.assertFalse(x != y)

        self.assertTrue(x <= y)
        self.assertTrue(x >= y)
        self.assertFalse(x < y)
        self.assertFalse(x > y)

        self.assertFalse(x == z)
        self.assertTrue(x != z)
        self.assertTrue(x < z)

        self.assertTrue(z != j)

        self.assertNotEqual(z, j)
        self.assertEqual(self.Q_(0, "meter"), self.Q_(0, "centimeter"))
        self.assertNotEqual(self.Q_(0, "meter"), self.Q_(0, "second"))

        self.assertLess(self.Q_(10, "meter"), self.Q_(5, "kilometer"))

    def test_quantity_comparison_convert(self):
        self.assertEqual(self.Q_(1000, "millimeter"), self.Q_(1, "meter"))
        self.assertEqual(
            self.Q_(1000, "millimeter/min"), self.Q_(1000 / 60, "millimeter/s")
        )

    def test_quantity_repr(self):
        x = self.Q_(4.2, UnitsContainer(meter=1))
        self.assertEqual(str(x), "4.2 meter")
        self.assertEqual(repr(x), "<Quantity(4.2, 'meter')>")

    def test_quantity_hash(self):
        x = self.Q_(4.2, "meter")
        x2 = self.Q_(4200, "millimeter")
        y = self.Q_(2, "second")
        z = self.Q_(0.5, "hertz")
        self.assertEqual(hash(x), hash(x2))

        # Dimensionless equality
        self.assertEqual(hash(y * z), hash(1.0))

        # Dimensionless equality from a different unit registry
        ureg2 = UnitRegistry(force_ndarray=self.FORCE_NDARRAY)
        y2 = ureg2.Quantity(2, "second")
        z2 = ureg2.Quantity(0.5, "hertz")
        self.assertEqual(hash(y * z), hash(y2 * z2))

    def test_quantity_format(self):
        x = self.Q_(4.12345678, UnitsContainer(meter=2, kilogram=1, second=-1))
        for spec, result in (
            ("{}", str(x)),
            ("{!s}", str(x)),
            ("{!r}", repr(x)),
            ("{.magnitude}", str(x.magnitude)),
            ("{.units}", str(x.units)),
            ("{.magnitude!s}", str(x.magnitude)),
            ("{.units!s}", str(x.units)),
            ("{.magnitude!r}", repr(x.magnitude)),
            ("{.units!r}", repr(x.units)),
            ("{:.4f}", f"{x.magnitude:.4f} {x.units!s}"),
            (
                "{:L}",
                r"4.12345678\ \frac{\mathrm{kilogram} \cdot \mathrm{meter}^{2}}{\mathrm{second}}",
            ),
            ("{:P}", "4.12345678 kilogram·meter²/second"),
            ("{:H}", "4.12345678 kilogram meter<sup>2</sup>/second"),
            ("{:C}", "4.12345678 kilogram*meter**2/second"),
            ("{:~}", "4.12345678 kg * m ** 2 / s"),
            (
                "{:L~}",
                r"4.12345678\ \frac{\mathrm{kg} \cdot \mathrm{m}^{2}}{\mathrm{s}}",
            ),
            ("{:P~}", "4.12345678 kg·m²/s"),
            ("{:H~}", "4.12345678 kg m<sup>2</sup>/s"),
            ("{:C~}", "4.12345678 kg*m**2/s"),
            ("{:Lx}", r"\SI[]{4.12345678}{\kilo\gram\meter\squared\per\second}"),
        ):
            with self.subTest(spec):
                self.assertEqual(spec.format(x), result)

        # Check the special case that prevents e.g. '3 1 / second'
        x = self.Q_(3, UnitsContainer(second=-1))
        self.assertEqual(f"{x}", "3 / second")

    @helpers.requires_numpy()
    def test_quantity_array_format(self):
        x = self.Q_(
            np.array([1e-16, 1.0000001, 10000000.0, 1e12, np.nan, np.inf]),
            "kg * m ** 2",
        )
        for spec, result in (
            ("{}", str(x)),
            ("{.magnitude}", str(x.magnitude)),
            (
                "{:e}",
                "[1.000000e-16 1.000000e+00 1.000000e+07 1.000000e+12 nan inf] kilogram * meter ** 2",
            ),
            (
                "{:E}",
                "[1.000000E-16 1.000000E+00 1.000000E+07 1.000000E+12 NAN INF] kilogram * meter ** 2",
            ),
            (
                "{:.2f}",
                "[0.00 1.00 10000000.00 1000000000000.00 nan inf] kilogram * meter ** 2",
            ),
            ("{:.2f~P}", "[0.00 1.00 10000000.00 1000000000000.00 nan inf] kg·m²"),
            ("{:g~P}", "[1e-16 1 1e+07 1e+12 nan inf] kg·m²"),
            (
                "{:.2f~H}",
                (
                    "<table><tbody><tr><th>Magnitude</th><td style='text-align:left;'>"
                    "<pre>[0.00 1.00 10000000.00 1000000000000.00 nan inf]</pre></td></tr>"
                    "<tr><th>Units</th><td style='text-align:left;'>kg m<sup>2</sup></td></tr>"
                    "</tbody></table>"
                ),
            ),
        ):
            with self.subTest(spec):
                self.assertEqual(spec.format(x), result)

    def test_format_compact(self):
        q1 = (200e-9 * self.ureg.s).to_compact()
        q1b = self.Q_(200.0, "nanosecond")
        self.assertAlmostEqual(q1.magnitude, q1b.magnitude)
        self.assertEqual(q1.units, q1b.units)

        q2 = (1e-2 * self.ureg("kg m/s^2")).to_compact("N")
        q2b = self.Q_(10.0, "millinewton")
        self.assertEqual(q2.magnitude, q2b.magnitude)
        self.assertEqual(q2.units, q2b.units)

        q3 = (-1000.0 * self.ureg("meters")).to_compact()
        q3b = self.Q_(-1.0, "kilometer")
        self.assertEqual(q3.magnitude, q3b.magnitude)
        self.assertEqual(q3.units, q3b.units)

        self.assertEqual(f"{q1:#.1f}", f"{q1b}")
        self.assertEqual(f"{q2:#.1f}", f"{q2b}")
        self.assertEqual(f"{q3:#.1f}", f"{q3b}")

    def test_default_formatting(self):
        ureg = UnitRegistry()
        x = ureg.Quantity(4.12345678, UnitsContainer(meter=2, kilogram=1, second=-1))
        for spec, result in (
            (
                "L",
                r"4.12345678\ \frac{\mathrm{kilogram} \cdot \mathrm{meter}^{2}}{\mathrm{second}}",
            ),
            ("P", "4.12345678 kilogram·meter²/second"),
            ("H", "4.12345678 kilogram meter<sup>2</sup>/second"),
            ("C", "4.12345678 kilogram*meter**2/second"),
            ("~", "4.12345678 kg * m ** 2 / s"),
            ("L~", r"4.12345678\ \frac{\mathrm{kg} \cdot \mathrm{m}^{2}}{\mathrm{s}}"),
            ("P~", "4.12345678 kg·m²/s"),
            ("H~", "4.12345678 kg m<sup>2</sup>/s"),
            ("C~", "4.12345678 kg*m**2/s"),
        ):
            with self.subTest(spec):
                ureg.default_format = spec
                self.assertEqual(f"{x}", result)

    def test_exponent_formatting(self):
        ureg = UnitRegistry()
        x = ureg.Quantity(1e20, "meter")
        self.assertEqual(f"{x:~H}", r"1×10<sup>20</sup> m")
        self.assertEqual(f"{x:~L}", r"1\times 10^{20}\ \mathrm{m}")
        self.assertEqual(f"{x:~P}", r"1×10²⁰ m")

        x /= 1e40
        self.assertEqual(f"{x:~H}", r"1×10<sup>-20</sup> m")
        self.assertEqual(f"{x:~L}", r"1\times 10^{-20}\ \mathrm{m}")
        self.assertEqual(f"{x:~P}", r"1×10⁻²⁰ m")

    def test_ipython(self):
        alltext = []

        class Pretty:
            @staticmethod
            def text(text):
                alltext.append(text)

            @classmethod
            def pretty(cls, data):
                try:
                    data._repr_pretty_(cls, False)
                except AttributeError:
                    alltext.append(str(data))

        ureg = UnitRegistry()
        x = 3.5 * ureg.Unit(UnitsContainer(meter=2, kilogram=1, second=-1))
        self.assertEqual(x._repr_html_(), "3.5 kilogram meter<sup>2</sup>/second")
        self.assertEqual(
            x._repr_latex_(),
            r"$3.5\ \frac{\mathrm{kilogram} \cdot "
            r"\mathrm{meter}^{2}}{\mathrm{second}}$",
        )
        x._repr_pretty_(Pretty, False)
        self.assertEqual("".join(alltext), "3.5 kilogram·meter²/second")
        ureg.default_format = "~"
        self.assertEqual(x._repr_html_(), "3.5 kg m<sup>2</sup>/s")
        self.assertEqual(
            x._repr_latex_(),
            r"$3.5\ \frac{\mathrm{kg} \cdot " r"\mathrm{m}^{2}}{\mathrm{s}}$",
        )
        alltext = []
        x._repr_pretty_(Pretty, False)
        self.assertEqual("".join(alltext), "3.5 kg·m²/s")

    def test_to_base_units(self):
        x = self.Q_("1*inch")
        self.assertQuantityAlmostEqual(x.to_base_units(), self.Q_(0.0254, "meter"))
        x = self.Q_("1*inch*inch")
        self.assertQuantityAlmostEqual(
            x.to_base_units(), self.Q_(0.0254 ** 2.0, "meter*meter")
        )
        x = self.Q_("1*inch/minute")
        self.assertQuantityAlmostEqual(
            x.to_base_units(), self.Q_(0.0254 / 60.0, "meter/second")
        )

    def test_convert(self):
        self.assertQuantityAlmostEqual(
            self.Q_("2 inch").to("meter"), self.Q_(2.0 * 0.0254, "meter")
        )
        self.assertQuantityAlmostEqual(
            self.Q_("2 meter").to("inch"), self.Q_(2.0 / 0.0254, "inch")
        )
        self.assertQuantityAlmostEqual(
            self.Q_("2 sidereal_year").to("second"), self.Q_(63116297.5325, "second")
        )
        self.assertQuantityAlmostEqual(
            self.Q_("2.54 centimeter/second").to("inch/second"),
            self.Q_("1 inch/second"),
        )
        self.assertAlmostEqual(self.Q_("2.54 centimeter").to("inch").magnitude, 1)
        self.assertAlmostEqual(self.Q_("2 second").to("millisecond").magnitude, 2000)

    @helpers.requires_numpy()
    def test_convert_numpy(self):

        # Conversions with single units take a different codepath than
        # Conversions with more than one unit.
        src_dst1 = UnitsContainer(meter=1), UnitsContainer(inch=1)
        src_dst2 = UnitsContainer(meter=1, second=-1), UnitsContainer(inch=1, minute=-1)
        for src, dst in (src_dst1, src_dst2):
            a = np.ones((3, 1))
            ac = np.ones((3, 1))

            q = self.Q_(a, src)
            qac = self.Q_(ac, src).to(dst)
            r = q.to(dst)
            self.assertQuantityAlmostEqual(qac, r)
            self.assertIsNot(r, q)
            self.assertIsNot(r._magnitude, a)

    def test_convert_from(self):
        x = self.Q_("2*inch")
        meter = self.ureg.meter

        # from quantity
        self.assertQuantityAlmostEqual(meter.from_(x), self.Q_(2.0 * 0.0254, "meter"))
        self.assertQuantityAlmostEqual(meter.m_from(x), 2.0 * 0.0254)

        # from unit
        self.assertQuantityAlmostEqual(
            meter.from_(self.ureg.inch), self.Q_(0.0254, "meter")
        )
        self.assertQuantityAlmostEqual(meter.m_from(self.ureg.inch), 0.0254)

        # from number
        self.assertQuantityAlmostEqual(
            meter.from_(2, strict=False), self.Q_(2.0, "meter")
        )
        self.assertQuantityAlmostEqual(meter.m_from(2, strict=False), 2.0)

        # from number (strict mode)
        self.assertRaises(ValueError, meter.from_, 2)
        self.assertRaises(ValueError, meter.m_from, 2)

    @helpers.requires_numpy()
    def test_retain_unit(self):
        # Test that methods correctly retain units and do not degrade into
        # ordinary ndarrays.  List contained in __copy_units.
        a = np.ones((3, 2))
        q = self.Q_(a, "km")
        self.assertEqual(q.u, q.reshape(2, 3).u)
        self.assertEqual(q.u, q.swapaxes(0, 1).u)
        self.assertEqual(q.u, q.mean().u)
        self.assertEqual(q.u, np.compress((q == q[0, 0]).any(0), q).u)

    def test_context_attr(self):
        self.assertEqual(self.ureg.meter, self.Q_(1, "meter"))

    def test_both_symbol(self):
        self.assertEqual(self.Q_(2, "ms"), self.Q_(2, "millisecond"))
        self.assertEqual(self.Q_(2, "cm"), self.Q_(2, "centimeter"))

    def test_dimensionless_units(self):
        self.assertAlmostEqual(
            self.Q_(360, "degree").to("radian").magnitude, 2 * math.pi
        )
        self.assertAlmostEqual(self.Q_(2 * math.pi, "radian"), self.Q_(360, "degree"))
        self.assertEqual(self.Q_(1, "radian").dimensionality, UnitsContainer())
        self.assertTrue(self.Q_(1, "radian").dimensionless)
        self.assertFalse(self.Q_(1, "radian").unitless)

        self.assertEqual(self.Q_(1, "meter") / self.Q_(1, "meter"), 1)
        self.assertEqual((self.Q_(1, "meter") / self.Q_(1, "mm")).to(""), 1000)

        self.assertEqual(self.Q_(10) // self.Q_(360, "degree"), 1)
        self.assertEqual(self.Q_(400, "degree") // self.Q_(2 * math.pi), 1)
        self.assertEqual(self.Q_(400, "degree") // (2 * math.pi), 1)
        self.assertEqual(7 // self.Q_(360, "degree"), 1)

    def test_offset(self):
        self.assertQuantityAlmostEqual(
            self.Q_(0, "kelvin").to("kelvin"), self.Q_(0, "kelvin")
        )
        self.assertQuantityAlmostEqual(
            self.Q_(0, "degC").to("kelvin"), self.Q_(273.15, "kelvin")
        )
        self.assertQuantityAlmostEqual(
            self.Q_(0, "degF").to("kelvin"), self.Q_(255.372222, "kelvin"), rtol=0.01
        )

        self.assertQuantityAlmostEqual(
            self.Q_(100, "kelvin").to("kelvin"), self.Q_(100, "kelvin")
        )
        self.assertQuantityAlmostEqual(
            self.Q_(100, "degC").to("kelvin"), self.Q_(373.15, "kelvin")
        )
        self.assertQuantityAlmostEqual(
            self.Q_(100, "degF").to("kelvin"),
            self.Q_(310.92777777, "kelvin"),
            rtol=0.01,
        )

        self.assertQuantityAlmostEqual(
            self.Q_(0, "kelvin").to("degC"), self.Q_(-273.15, "degC")
        )
        self.assertQuantityAlmostEqual(
            self.Q_(100, "kelvin").to("degC"), self.Q_(-173.15, "degC")
        )
        self.assertQuantityAlmostEqual(
            self.Q_(0, "kelvin").to("degF"), self.Q_(-459.67, "degF"), rtol=0.01
        )
        self.assertQuantityAlmostEqual(
            self.Q_(100, "kelvin").to("degF"), self.Q_(-279.67, "degF"), rtol=0.01
        )

        self.assertQuantityAlmostEqual(
            self.Q_(32, "degF").to("degC"), self.Q_(0, "degC"), atol=0.01
        )
        self.assertQuantityAlmostEqual(
            self.Q_(100, "degC").to("degF"), self.Q_(212, "degF"), atol=0.01
        )

        self.assertQuantityAlmostEqual(
            self.Q_(54, "degF").to("degC"), self.Q_(12.2222, "degC"), atol=0.01
        )
        self.assertQuantityAlmostEqual(
            self.Q_(12, "degC").to("degF"), self.Q_(53.6, "degF"), atol=0.01
        )

        self.assertQuantityAlmostEqual(
            self.Q_(12, "kelvin").to("degC"), self.Q_(-261.15, "degC"), atol=0.01
        )
        self.assertQuantityAlmostEqual(
            self.Q_(12, "degC").to("kelvin"), self.Q_(285.15, "kelvin"), atol=0.01
        )

        self.assertQuantityAlmostEqual(
            self.Q_(12, "kelvin").to("degR"), self.Q_(21.6, "degR"), atol=0.01
        )
        self.assertQuantityAlmostEqual(
            self.Q_(12, "degR").to("kelvin"), self.Q_(6.66666667, "kelvin"), atol=0.01
        )

        self.assertQuantityAlmostEqual(
            self.Q_(12, "degC").to("degR"), self.Q_(513.27, "degR"), atol=0.01
        )
        self.assertQuantityAlmostEqual(
            self.Q_(12, "degR").to("degC"), self.Q_(-266.483333, "degC"), atol=0.01
        )

    def test_offset_delta(self):
        self.assertQuantityAlmostEqual(
            self.Q_(0, "delta_degC").to("kelvin"), self.Q_(0, "kelvin")
        )
        self.assertQuantityAlmostEqual(
            self.Q_(0, "delta_degF").to("kelvin"), self.Q_(0, "kelvin"), rtol=0.01
        )

        self.assertQuantityAlmostEqual(
            self.Q_(100, "kelvin").to("delta_degC"), self.Q_(100, "delta_degC")
        )
        self.assertQuantityAlmostEqual(
            self.Q_(100, "kelvin").to("delta_degF"),
            self.Q_(180, "delta_degF"),
            rtol=0.01,
        )
        self.assertQuantityAlmostEqual(
            self.Q_(100, "delta_degF").to("kelvin"),
            self.Q_(55.55555556, "kelvin"),
            rtol=0.01,
        )
        self.assertQuantityAlmostEqual(
            self.Q_(100, "delta_degC").to("delta_degF"),
            self.Q_(180, "delta_degF"),
            rtol=0.01,
        )
        self.assertQuantityAlmostEqual(
            self.Q_(100, "delta_degF").to("delta_degC"),
            self.Q_(55.55555556, "delta_degC"),
            rtol=0.01,
        )

        self.assertQuantityAlmostEqual(
            self.Q_(12.3, "delta_degC").to("delta_degF"),
            self.Q_(22.14, "delta_degF"),
            rtol=0.01,
        )

    def test_pickle(self):
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            for magnitude, unit in ((32, ""), (2.4, ""), (32, "m/s"), (2.4, "m/s")):
                with self.subTest(protocol=protocol, magnitude=magnitude, unit=unit):
                    q1 = self.Q_(magnitude, unit)
                    q2 = pickle.loads(pickle.dumps(q1, protocol))
                    self.assertEqual(q1, q2)

    @helpers.requires_numpy()
    def test_from_sequence(self):
        u_array_ref = self.Q_([200, 1000], "g")
        u_array_ref_reversed = self.Q_([1000, 200], "g")
        u_seq = [self.Q_("200g"), self.Q_("1kg")]
        u_seq_reversed = u_seq[::-1]

        u_array = self.Q_.from_sequence(u_seq)
        self.assertTrue(all(u_array == u_array_ref))

        u_array_2 = self.Q_.from_sequence(u_seq_reversed)
        self.assertTrue(all(u_array_2 == u_array_ref_reversed))
        self.assertFalse(u_array_2.u == u_array_ref_reversed.u)

        u_array_3 = self.Q_.from_sequence(u_seq_reversed, units="g")
        self.assertTrue(all(u_array_3 == u_array_ref_reversed))
        self.assertTrue(u_array_3.u == u_array_ref_reversed.u)

        with self.assertRaises(ValueError):
            self.Q_.from_sequence([])

        u_array_5 = self.Q_.from_list(u_seq)
        self.assertTrue(all(u_array_5 == u_array_ref))

    @helpers.requires_numpy()
    def test_iter(self):
        # Verify that iteration gives element as Quantity with same units
        x = self.Q_([0, 1, 2, 3], "m")
        self.assertQuantityEqual(next(iter(x)), self.Q_(0, "m"))

    def test_notiter(self):
        # Verify that iter() crashes immediately, without needing to draw any
        # element from it, if the magnitude isn't iterable
        x = self.Q_(1, "m")
        with self.assertRaises(TypeError):
            iter(x)

    @helpers.requires_array_function_protocol()
    def test_no_longer_array_function_warning_on_creation(self):
        # Test that warning is no longer raised on first creation
        with warnings.catch_warnings():
            warnings.filterwarnings("error")
            self.Q_([])

    @helpers.requires_not_numpy()
    def test_no_ndarray_coercion_without_numpy(self):
        self.assertRaises(ValueError, self.Q_(1, "m").__array__)

    @patch("pint.compat.upcast_types", [FakeWrapper])
    def test_upcast_type_rejection_on_creation(self):
        self.assertRaises(TypeError, self.Q_, FakeWrapper(42), "m")
        self.assertEqual(FakeWrapper(self.Q_(42, "m")).q, self.Q_(42, "m"))


class TestQuantityToCompact(QuantityTestCase):
    def assertQuantityAlmostIdentical(self, q1, q2):
        self.assertEqual(q1.units, q2.units)
        self.assertAlmostEqual(q1.magnitude, q2.magnitude)

    def compareQuantity_compact(self, q, expected_compact, unit=None):
        self.assertQuantityAlmostIdentical(q.to_compact(unit=unit), expected_compact)

    def test_dimensionally_simple_units(self):
        ureg = self.ureg
        self.compareQuantity_compact(1 * ureg.m, 1 * ureg.m)
        self.compareQuantity_compact(1e-9 * ureg.m, 1 * ureg.nm)

    def test_power_units(self):
        ureg = self.ureg
        self.compareQuantity_compact(900 * ureg.m ** 2, 900 * ureg.m ** 2)
        self.compareQuantity_compact(1e7 * ureg.m ** 2, 10 * ureg.km ** 2)

    def test_inverse_units(self):
        ureg = self.ureg
        self.compareQuantity_compact(1 / ureg.m, 1 / ureg.m)
        self.compareQuantity_compact(100e9 / ureg.m, 100 / ureg.nm)

    def test_inverse_square_units(self):
        ureg = self.ureg
        self.compareQuantity_compact(1 / ureg.m ** 2, 1 / ureg.m ** 2)
        self.compareQuantity_compact(1e11 / ureg.m ** 2, 1e5 / ureg.mm ** 2)

    def test_fractional_units(self):
        ureg = self.ureg
        # Typing denominator first to provoke potential error
        self.compareQuantity_compact(20e3 * ureg("hr^(-1) m"), 20 * ureg.km / ureg.hr)

    def test_fractional_exponent_units(self):
        ureg = self.ureg
        self.compareQuantity_compact(1 * ureg.m ** 0.5, 1 * ureg.m ** 0.5)
        self.compareQuantity_compact(1e-2 * ureg.m ** 0.5, 10 * ureg.um ** 0.5)

    def test_derived_units(self):
        ureg = self.ureg
        self.compareQuantity_compact(0.5 * ureg.megabyte, 500 * ureg.kilobyte)
        self.compareQuantity_compact(1e-11 * ureg.N, 10 * ureg.pN)

    def test_unit_parameter(self):
        ureg = self.ureg
        self.compareQuantity_compact(
            self.Q_(100e-9, "kg m / s^2"), 100 * ureg.nN, ureg.N
        )
        self.compareQuantity_compact(
            self.Q_(101.3e3, "kg/m/s^2"), 101.3 * ureg.kPa, ureg.Pa
        )

    def test_limits_magnitudes(self):
        ureg = self.ureg
        self.compareQuantity_compact(0 * ureg.m, 0 * ureg.m)
        self.compareQuantity_compact(float("inf") * ureg.m, float("inf") * ureg.m)

    def test_nonnumeric_magnitudes(self):
        ureg = self.ureg
        x = "some string" * ureg.m
        with self.assertWarns(RuntimeWarning):
            self.compareQuantity_compact(x, x)

    def test_very_large_to_compact(self):
        # This should not raise an IndexError
        self.compareQuantity_compact(
            self.Q_(10000, "yottameter"), self.Q_(10 ** 28, "meter").to_compact()
        )


class TestQuantityBasicMath(QuantityTestCase):

    FORCE_NDARRAY = False

    def _test_inplace(self, operator, value1, value2, expected_result, unit=None):
        if isinstance(value1, str):
            value1 = self.Q_(value1)
        if isinstance(value2, str):
            value2 = self.Q_(value2)
        if isinstance(expected_result, str):
            expected_result = self.Q_(expected_result)

        if unit is not None:
            value1 = value1 * unit
            value2 = value2 * unit
            expected_result = expected_result * unit

        value1 = copy.copy(value1)
        value2 = copy.copy(value2)
        id1 = id(value1)
        id2 = id(value2)
        value1 = operator(value1, value2)
        value2_cpy = copy.copy(value2)
        self.assertQuantityAlmostEqual(value1, expected_result)
        self.assertEqual(id1, id(value1))
        self.assertQuantityAlmostEqual(value2, value2_cpy)
        self.assertEqual(id2, id(value2))

    def _test_not_inplace(self, operator, value1, value2, expected_result, unit=None):
        if isinstance(value1, str):
            value1 = self.Q_(value1)
        if isinstance(value2, str):
            value2 = self.Q_(value2)
        if isinstance(expected_result, str):
            expected_result = self.Q_(expected_result)

        if unit is not None:
            value1 = value1 * unit
            value2 = value2 * unit
            expected_result = expected_result * unit

        id1 = id(value1)
        id2 = id(value2)

        value1_cpy = copy.copy(value1)
        value2_cpy = copy.copy(value2)

        result = operator(value1, value2)

        self.assertQuantityAlmostEqual(expected_result, result)
        self.assertQuantityAlmostEqual(value1, value1_cpy)
        self.assertQuantityAlmostEqual(value2, value2_cpy)
        self.assertNotEqual(id(result), id1)
        self.assertNotEqual(id(result), id2)

    def _test_quantity_add_sub(self, unit, func):
        x = self.Q_(unit, "centimeter")
        y = self.Q_(unit, "inch")
        z = self.Q_(unit, "second")
        a = self.Q_(unit, None)

        func(op.add, x, x, self.Q_(unit + unit, "centimeter"))
        func(op.add, x, y, self.Q_(unit + 2.54 * unit, "centimeter"))
        func(op.add, y, x, self.Q_(unit + unit / (2.54 * unit), "inch"))
        func(op.add, a, unit, self.Q_(unit + unit, None))
        self.assertRaises(DimensionalityError, op.add, 10, x)
        self.assertRaises(DimensionalityError, op.add, x, 10)
        self.assertRaises(DimensionalityError, op.add, x, z)

        func(op.sub, x, x, self.Q_(unit - unit, "centimeter"))
        func(op.sub, x, y, self.Q_(unit - 2.54 * unit, "centimeter"))
        func(op.sub, y, x, self.Q_(unit - unit / (2.54 * unit), "inch"))
        func(op.sub, a, unit, self.Q_(unit - unit, None))
        self.assertRaises(DimensionalityError, op.sub, 10, x)
        self.assertRaises(DimensionalityError, op.sub, x, 10)
        self.assertRaises(DimensionalityError, op.sub, x, z)

    def _test_quantity_iadd_isub(self, unit, func):
        x = self.Q_(unit, "centimeter")
        y = self.Q_(unit, "inch")
        z = self.Q_(unit, "second")
        a = self.Q_(unit, None)

        func(op.iadd, x, x, self.Q_(unit + unit, "centimeter"))
        func(op.iadd, x, y, self.Q_(unit + 2.54 * unit, "centimeter"))
        func(op.iadd, y, x, self.Q_(unit + unit / 2.54, "inch"))
        func(op.iadd, a, unit, self.Q_(unit + unit, None))
        self.assertRaises(DimensionalityError, op.iadd, 10, x)
        self.assertRaises(DimensionalityError, op.iadd, x, 10)
        self.assertRaises(DimensionalityError, op.iadd, x, z)

        func(op.isub, x, x, self.Q_(unit - unit, "centimeter"))
        func(op.isub, x, y, self.Q_(unit - 2.54, "centimeter"))
        func(op.isub, y, x, self.Q_(unit - unit / 2.54, "inch"))
        func(op.isub, a, unit, self.Q_(unit - unit, None))
        self.assertRaises(DimensionalityError, op.sub, 10, x)
        self.assertRaises(DimensionalityError, op.sub, x, 10)
        self.assertRaises(DimensionalityError, op.sub, x, z)

    def _test_quantity_mul_div(self, unit, func):
        func(op.mul, unit * 10.0, "4.2*meter", "42*meter", unit)
        func(op.mul, "4.2*meter", unit * 10.0, "42*meter", unit)
        func(op.mul, "4.2*meter", "10*inch", "42*meter*inch", unit)
        func(op.truediv, unit * 42, "4.2*meter", "10/meter", unit)
        func(op.truediv, "4.2*meter", unit * 10.0, "0.42*meter", unit)
        func(op.truediv, "4.2*meter", "10*inch", "0.42*meter/inch", unit)

    def _test_quantity_imul_idiv(self, unit, func):
        # func(op.imul, 10.0, '4.2*meter', '42*meter')
        func(op.imul, "4.2*meter", 10.0, "42*meter", unit)
        func(op.imul, "4.2*meter", "10*inch", "42*meter*inch", unit)
        # func(op.truediv, 42, '4.2*meter', '10/meter')
        func(op.itruediv, "4.2*meter", unit * 10.0, "0.42*meter", unit)
        func(op.itruediv, "4.2*meter", "10*inch", "0.42*meter/inch", unit)

    def _test_quantity_floordiv(self, unit, func):
        a = self.Q_("10*meter")
        b = self.Q_("3*second")
        self.assertRaises(DimensionalityError, op.floordiv, a, b)
        self.assertRaises(DimensionalityError, op.floordiv, 3, b)
        self.assertRaises(DimensionalityError, op.floordiv, a, 3)
        self.assertRaises(DimensionalityError, op.ifloordiv, a, b)
        self.assertRaises(DimensionalityError, op.ifloordiv, 3, b)
        self.assertRaises(DimensionalityError, op.ifloordiv, a, 3)
        func(op.floordiv, unit * 10.0, "4.2*meter/meter", 2, unit)
        func(op.floordiv, "10*meter", "4.2*inch", 93, unit)

    def _test_quantity_mod(self, unit, func):
        a = self.Q_("10*meter")
        b = self.Q_("3*second")
        self.assertRaises(DimensionalityError, op.mod, a, b)
        self.assertRaises(DimensionalityError, op.mod, 3, b)
        self.assertRaises(DimensionalityError, op.mod, a, 3)
        self.assertRaises(DimensionalityError, op.imod, a, b)
        self.assertRaises(DimensionalityError, op.imod, 3, b)
        self.assertRaises(DimensionalityError, op.imod, a, 3)
        func(op.mod, unit * 10.0, "4.2*meter/meter", 1.6, unit)

    def _test_quantity_ifloordiv(self, unit, func):
        func(op.ifloordiv, 10.0, "4.2*meter/meter", 2, unit)
        func(op.ifloordiv, "10*meter", "4.2*inch", 93, unit)

    def _test_quantity_divmod_one(self, a, b):
        if isinstance(a, str):
            a = self.Q_(a)
        if isinstance(b, str):
            b = self.Q_(b)

        q, r = divmod(a, b)
        self.assertEqual(q, a // b)
        self.assertEqual(r, a % b)
        self.assertEqual(a, (q * b) + r)
        self.assertEqual(q, math.floor(q))
        if b > (0 * b):
            self.assertTrue((0 * b) <= r < b)
        else:
            self.assertTrue((0 * b) >= r > b)
        if isinstance(a, self.Q_):
            self.assertEqual(r.units, a.units)
        else:
            self.assertTrue(r.unitless)
        self.assertTrue(q.unitless)

        copy_a = copy.copy(a)
        a %= b
        self.assertEqual(a, r)
        copy_a //= b
        self.assertEqual(copy_a, q)

    def _test_quantity_divmod(self):
        self._test_quantity_divmod_one("10*meter", "4.2*inch")
        self._test_quantity_divmod_one("-10*meter", "4.2*inch")
        self._test_quantity_divmod_one("-10*meter", "-4.2*inch")
        self._test_quantity_divmod_one("10*meter", "-4.2*inch")

        self._test_quantity_divmod_one("400*degree", "3")
        self._test_quantity_divmod_one("4", "180 degree")
        self._test_quantity_divmod_one(4, "180 degree")
        self._test_quantity_divmod_one("20", 4)
        self._test_quantity_divmod_one("300*degree", "100 degree")

        a = self.Q_("10*meter")
        b = self.Q_("3*second")
        self.assertRaises(DimensionalityError, divmod, a, b)
        self.assertRaises(DimensionalityError, divmod, 3, b)
        self.assertRaises(DimensionalityError, divmod, a, 3)

    def _test_numeric(self, unit, ifunc):
        self._test_quantity_add_sub(unit, self._test_not_inplace)
        self._test_quantity_iadd_isub(unit, ifunc)
        self._test_quantity_mul_div(unit, self._test_not_inplace)
        self._test_quantity_imul_idiv(unit, ifunc)
        self._test_quantity_floordiv(unit, self._test_not_inplace)
        self._test_quantity_mod(unit, self._test_not_inplace)
        self._test_quantity_divmod()
        # self._test_quantity_ifloordiv(unit, ifunc)

    def test_float(self):
        self._test_numeric(1.0, self._test_not_inplace)

    def test_fraction(self):
        import fractions

        self._test_numeric(fractions.Fraction(1, 1), self._test_not_inplace)

    @helpers.requires_numpy()
    def test_nparray(self):
        self._test_numeric(np.ones((1, 3)), self._test_inplace)

    def test_quantity_abs_round(self):

        x = self.Q_(-4.2, "meter")
        y = self.Q_(4.2, "meter")

        for fun in (abs, round, op.pos, op.neg):
            zx = self.Q_(fun(x.magnitude), "meter")
            zy = self.Q_(fun(y.magnitude), "meter")
            rx = fun(x)
            ry = fun(y)
            self.assertEqual(rx, zx, "while testing {0}".format(fun))
            self.assertEqual(ry, zy, "while testing {0}".format(fun))
            self.assertIsNot(rx, zx, "while testing {0}".format(fun))
            self.assertIsNot(ry, zy, "while testing {0}".format(fun))

    def test_quantity_float_complex(self):
        x = self.Q_(-4.2, None)
        y = self.Q_(4.2, None)
        z = self.Q_(1, "meter")
        for fun in (float, complex):
            self.assertEqual(fun(x), fun(x.magnitude))
            self.assertEqual(fun(y), fun(y.magnitude))
            self.assertRaises(DimensionalityError, fun, z)


class TestQuantityNeutralAdd(QuantityTestCase):
    """Addition to zero or NaN is allowed between a Quantity and a non-Quantity
    """

    FORCE_NDARRAY = False

    def test_bare_zero(self):
        v = self.Q_(2.0, "m")
        self.assertEqual(v + 0, v)
        self.assertEqual(v - 0, v)
        self.assertEqual(0 + v, v)
        self.assertEqual(0 - v, -v)

    def test_bare_zero_inplace(self):
        v = self.Q_(2.0, "m")
        v2 = self.Q_(2.0, "m")
        v2 += 0
        self.assertEqual(v2, v)
        v2 = self.Q_(2.0, "m")
        v2 -= 0
        self.assertEqual(v2, v)
        v2 = 0
        v2 += v
        self.assertEqual(v2, v)
        v2 = 0
        v2 -= v
        self.assertEqual(v2, -v)

    def test_bare_nan(self):
        v = self.Q_(2.0, "m")
        self.assertQuantityEqual(v + math.nan, self.Q_(math.nan, v.units))
        self.assertQuantityEqual(v - math.nan, self.Q_(math.nan, v.units))
        self.assertQuantityEqual(math.nan + v, self.Q_(math.nan, v.units))
        self.assertQuantityEqual(math.nan - v, self.Q_(math.nan, v.units))

    def test_bare_nan_inplace(self):
        v = self.Q_(2.0, "m")
        v2 = self.Q_(2.0, "m")
        v2 += math.nan
        self.assertQuantityEqual(v2, self.Q_(math.nan, v.units))
        v2 = self.Q_(2.0, "m")
        v2 -= math.nan
        self.assertQuantityEqual(v2, self.Q_(math.nan, v.units))
        v2 = math.nan
        v2 += v
        self.assertQuantityEqual(v2, self.Q_(math.nan, v.units))
        v2 = math.nan
        v2 -= v
        self.assertQuantityEqual(v2, self.Q_(math.nan, v.units))

    @helpers.requires_numpy()
    def test_bare_zero_or_nan_numpy(self):
        z = np.array([0.0, np.nan])
        v = self.Q_([1.0, 2.0], "m")
        e = self.Q_([1.0, np.nan], "m")
        self.assertQuantityEqual(z + v, e)
        self.assertQuantityEqual(z - v, -e)
        self.assertQuantityEqual(v + z, e)
        self.assertQuantityEqual(v - z, e)

        # If any element is non-zero and non-NaN, raise DimensionalityError
        nz = np.array([0.0, 1.0])
        with self.assertRaises(DimensionalityError):
            nz + v
        with self.assertRaises(DimensionalityError):
            nz - v
        with self.assertRaises(DimensionalityError):
            v + nz
        with self.assertRaises(DimensionalityError):
            v - nz

        # Mismatched shape
        z = np.array([0.0, np.nan, 0.0])
        v = self.Q_([1.0, 2.0], "m")
        for x, y in ((z, v), (v, z)):
            with self.assertRaises(ValueError):
                x + y
            with self.assertRaises(ValueError):
                x - y

    @helpers.requires_numpy()
    def test_bare_zero_or_nan_numpy_inplace(self):
        z = np.array([0.0, np.nan])
        v = self.Q_([1.0, 2.0], "m")
        e = self.Q_([1.0, np.nan], "m")
        v += z
        self.assertQuantityEqual(v, e)
        v = self.Q_([1.0, 2.0], "m")
        v -= z
        self.assertQuantityEqual(v, e)
        v = self.Q_([1.0, 2.0], "m")
        z = np.array([0.0, np.nan])
        z += v
        self.assertQuantityEqual(z, e)
        v = self.Q_([1.0, 2.0], "m")
        z = np.array([0.0, np.nan])
        z -= v
        self.assertQuantityEqual(z, -e)


class TestDimensions(QuantityTestCase):

    FORCE_NDARRAY = False

    def test_get_dimensionality(self):
        get = self.ureg.get_dimensionality
        self.assertEqual(get("[time]"), UnitsContainer({"[time]": 1}))
        self.assertEqual(
            get(UnitsContainer({"[time]": 1})), UnitsContainer({"[time]": 1})
        )
        self.assertEqual(get("seconds"), UnitsContainer({"[time]": 1}))
        self.assertEqual(
            get(UnitsContainer({"seconds": 1})), UnitsContainer({"[time]": 1})
        )
        self.assertEqual(get("[speed]"), UnitsContainer({"[length]": 1, "[time]": -1}))
        self.assertEqual(
            get("[acceleration]"), UnitsContainer({"[length]": 1, "[time]": -2})
        )

    def test_dimensionality(self):
        x = self.Q_(42, "centimeter")
        x.to_base_units()
        x = self.Q_(42, "meter*second")
        self.assertEqual(
            x.dimensionality, UnitsContainer({"[length]": 1.0, "[time]": 1.0})
        )
        x = self.Q_(42, "meter*second*second")
        self.assertEqual(
            x.dimensionality, UnitsContainer({"[length]": 1.0, "[time]": 2.0})
        )
        x = self.Q_(42, "inch*second*second")
        self.assertEqual(
            x.dimensionality, UnitsContainer({"[length]": 1.0, "[time]": 2.0})
        )
        self.assertTrue(self.Q_(42, None).dimensionless)
        self.assertFalse(self.Q_(42, "meter").dimensionless)
        self.assertTrue((self.Q_(42, "meter") / self.Q_(1, "meter")).dimensionless)
        self.assertFalse((self.Q_(42, "meter") / self.Q_(1, "second")).dimensionless)
        self.assertTrue((self.Q_(42, "meter") / self.Q_(1, "inch")).dimensionless)

    def test_inclusion(self):
        dim = self.Q_(42, "meter").dimensionality
        self.assertTrue("[length]" in dim)
        self.assertFalse("[time]" in dim)
        dim = (self.Q_(42, "meter") / self.Q_(11, "second")).dimensionality
        self.assertTrue("[length]" in dim)
        self.assertTrue("[time]" in dim)
        dim = self.Q_(20.785, "J/(mol)").dimensionality
        for dimension in ("[length]", "[mass]", "[substance]", "[time]"):
            self.assertTrue(dimension in dim)
        self.assertFalse("[angle]" in dim)


class TestQuantityWithDefaultRegistry(TestDimensions):
    @classmethod
    def setUpClass(cls):
        from pint import _DEFAULT_REGISTRY

        cls.ureg = _DEFAULT_REGISTRY
        cls.Q_ = cls.ureg.Quantity


class TestDimensionsWithDefaultRegistry(TestDimensions):
    @classmethod
    def setUpClass(cls):
        from pint import _DEFAULT_REGISTRY

        cls.ureg = _DEFAULT_REGISTRY
        cls.Q_ = cls.ureg.Quantity


class TestOffsetUnitMath(QuantityTestCase, ParameterizedTestCase):
    def setup(self):
        self.ureg.autoconvert_offset_to_baseunit = False
        self.ureg.default_as_delta = True

    additions = [
        # --- input tuple -------------------- | -- expected result --
        (((100, "kelvin"), (10, "kelvin")), (110, "kelvin")),
        (((100, "kelvin"), (10, "degC")), "error"),
        (((100, "kelvin"), (10, "degF")), "error"),
        (((100, "kelvin"), (10, "degR")), (105.56, "kelvin")),
        (((100, "kelvin"), (10, "delta_degC")), (110, "kelvin")),
        (((100, "kelvin"), (10, "delta_degF")), (105.56, "kelvin")),
        (((100, "degC"), (10, "kelvin")), "error"),
        (((100, "degC"), (10, "degC")), "error"),
        (((100, "degC"), (10, "degF")), "error"),
        (((100, "degC"), (10, "degR")), "error"),
        (((100, "degC"), (10, "delta_degC")), (110, "degC")),
        (((100, "degC"), (10, "delta_degF")), (105.56, "degC")),
        (((100, "degF"), (10, "kelvin")), "error"),
        (((100, "degF"), (10, "degC")), "error"),
        (((100, "degF"), (10, "degF")), "error"),
        (((100, "degF"), (10, "degR")), "error"),
        (((100, "degF"), (10, "delta_degC")), (118, "degF")),
        (((100, "degF"), (10, "delta_degF")), (110, "degF")),
        (((100, "degR"), (10, "kelvin")), (118, "degR")),
        (((100, "degR"), (10, "degC")), "error"),
        (((100, "degR"), (10, "degF")), "error"),
        (((100, "degR"), (10, "degR")), (110, "degR")),
        (((100, "degR"), (10, "delta_degC")), (118, "degR")),
        (((100, "degR"), (10, "delta_degF")), (110, "degR")),
        (((100, "delta_degC"), (10, "kelvin")), (110, "kelvin")),
        (((100, "delta_degC"), (10, "degC")), (110, "degC")),
        (((100, "delta_degC"), (10, "degF")), (190, "degF")),
        (((100, "delta_degC"), (10, "degR")), (190, "degR")),
        (((100, "delta_degC"), (10, "delta_degC")), (110, "delta_degC")),
        (((100, "delta_degC"), (10, "delta_degF")), (105.56, "delta_degC")),
        (((100, "delta_degF"), (10, "kelvin")), (65.56, "kelvin")),
        (((100, "delta_degF"), (10, "degC")), (65.56, "degC")),
        (((100, "delta_degF"), (10, "degF")), (110, "degF")),
        (((100, "delta_degF"), (10, "degR")), (110, "degR")),
        (((100, "delta_degF"), (10, "delta_degC")), (118, "delta_degF")),
        (((100, "delta_degF"), (10, "delta_degF")), (110, "delta_degF")),
    ]

    @ParameterizedTestCase.parameterize(("input", "expected_output"), additions)
    def test_addition(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = False
        qin1, qin2 = input_tuple
        q1, q2 = self.Q_(*qin1), self.Q_(*qin2)
        # update input tuple with new values to have correct values on failure
        input_tuple = q1, q2
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.add, q1, q2)
        else:
            expected = self.Q_(*expected)
            self.assertEqual(op.add(q1, q2).units, expected.units)
            self.assertQuantityAlmostEqual(op.add(q1, q2), expected, atol=0.01)

    @helpers.requires_numpy()
    @ParameterizedTestCase.parameterize(("input", "expected_output"), additions)
    def test_inplace_addition(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = False
        (q1v, q1u), (q2v, q2u) = input_tuple
        # update input tuple with new values to have correct values on failure
        input_tuple = (
            (np.array([q1v] * 2, dtype=np.float), q1u),
            (np.array([q2v] * 2, dtype=np.float), q2u),
        )
        Q_ = self.Q_
        qin1, qin2 = input_tuple
        q1, q2 = Q_(*qin1), Q_(*qin2)
        q1_cp = copy.copy(q1)
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.iadd, q1_cp, q2)
        else:
            expected = np.array([expected[0]] * 2, dtype=np.float), expected[1]
            self.assertEqual(op.iadd(q1_cp, q2).units, Q_(*expected).units)
            q1_cp = copy.copy(q1)
            self.assertQuantityAlmostEqual(op.iadd(q1_cp, q2), Q_(*expected), atol=0.01)

    subtractions = [
        (((100, "kelvin"), (10, "kelvin")), (90, "kelvin")),
        (((100, "kelvin"), (10, "degC")), (-183.15, "kelvin")),
        (((100, "kelvin"), (10, "degF")), (-160.93, "kelvin")),
        (((100, "kelvin"), (10, "degR")), (94.44, "kelvin")),
        (((100, "kelvin"), (10, "delta_degC")), (90, "kelvin")),
        (((100, "kelvin"), (10, "delta_degF")), (94.44, "kelvin")),
        (((100, "degC"), (10, "kelvin")), (363.15, "delta_degC")),
        (((100, "degC"), (10, "degC")), (90, "delta_degC")),
        (((100, "degC"), (10, "degF")), (112.22, "delta_degC")),
        (((100, "degC"), (10, "degR")), (367.59, "delta_degC")),
        (((100, "degC"), (10, "delta_degC")), (90, "degC")),
        (((100, "degC"), (10, "delta_degF")), (94.44, "degC")),
        (((100, "degF"), (10, "kelvin")), (541.67, "delta_degF")),
        (((100, "degF"), (10, "degC")), (50, "delta_degF")),
        (((100, "degF"), (10, "degF")), (90, "delta_degF")),
        (((100, "degF"), (10, "degR")), (549.67, "delta_degF")),
        (((100, "degF"), (10, "delta_degC")), (82, "degF")),
        (((100, "degF"), (10, "delta_degF")), (90, "degF")),
        (((100, "degR"), (10, "kelvin")), (82, "degR")),
        (((100, "degR"), (10, "degC")), (-409.67, "degR")),
        (((100, "degR"), (10, "degF")), (-369.67, "degR")),
        (((100, "degR"), (10, "degR")), (90, "degR")),
        (((100, "degR"), (10, "delta_degC")), (82, "degR")),
        (((100, "degR"), (10, "delta_degF")), (90, "degR")),
        (((100, "delta_degC"), (10, "kelvin")), (90, "kelvin")),
        (((100, "delta_degC"), (10, "degC")), (90, "degC")),
        (((100, "delta_degC"), (10, "degF")), (170, "degF")),
        (((100, "delta_degC"), (10, "degR")), (170, "degR")),
        (((100, "delta_degC"), (10, "delta_degC")), (90, "delta_degC")),
        (((100, "delta_degC"), (10, "delta_degF")), (94.44, "delta_degC")),
        (((100, "delta_degF"), (10, "kelvin")), (45.56, "kelvin")),
        (((100, "delta_degF"), (10, "degC")), (45.56, "degC")),
        (((100, "delta_degF"), (10, "degF")), (90, "degF")),
        (((100, "delta_degF"), (10, "degR")), (90, "degR")),
        (((100, "delta_degF"), (10, "delta_degC")), (82, "delta_degF")),
        (((100, "delta_degF"), (10, "delta_degF")), (90, "delta_degF")),
    ]

    @ParameterizedTestCase.parameterize(("input", "expected_output"), subtractions)
    def test_subtraction(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = False
        qin1, qin2 = input_tuple
        q1, q2 = self.Q_(*qin1), self.Q_(*qin2)
        input_tuple = q1, q2
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.sub, q1, q2)
        else:
            expected = self.Q_(*expected)
            self.assertEqual(op.sub(q1, q2).units, expected.units)
            self.assertQuantityAlmostEqual(op.sub(q1, q2), expected, atol=0.01)

    #    @unittest.expectedFailure
    @helpers.requires_numpy()
    @ParameterizedTestCase.parameterize(("input", "expected_output"), subtractions)
    def test_inplace_subtraction(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = False
        (q1v, q1u), (q2v, q2u) = input_tuple
        # update input tuple with new values to have correct values on failure
        input_tuple = (
            (np.array([q1v] * 2, dtype=np.float), q1u),
            (np.array([q2v] * 2, dtype=np.float), q2u),
        )
        Q_ = self.Q_
        qin1, qin2 = input_tuple
        q1, q2 = Q_(*qin1), Q_(*qin2)
        q1_cp = copy.copy(q1)
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.isub, q1_cp, q2)
        else:
            expected = np.array([expected[0]] * 2, dtype=np.float), expected[1]
            self.assertEqual(op.isub(q1_cp, q2).units, Q_(*expected).units)
            q1_cp = copy.copy(q1)
            self.assertQuantityAlmostEqual(op.isub(q1_cp, q2), Q_(*expected), atol=0.01)

    multiplications = [
        (((100, "kelvin"), (10, "kelvin")), (1000, "kelvin**2")),
        (((100, "kelvin"), (10, "degC")), "error"),
        (((100, "kelvin"), (10, "degF")), "error"),
        (((100, "kelvin"), (10, "degR")), (1000, "kelvin*degR")),
        (((100, "kelvin"), (10, "delta_degC")), (1000, "kelvin*delta_degC")),
        (((100, "kelvin"), (10, "delta_degF")), (1000, "kelvin*delta_degF")),
        (((100, "degC"), (10, "kelvin")), "error"),
        (((100, "degC"), (10, "degC")), "error"),
        (((100, "degC"), (10, "degF")), "error"),
        (((100, "degC"), (10, "degR")), "error"),
        (((100, "degC"), (10, "delta_degC")), "error"),
        (((100, "degC"), (10, "delta_degF")), "error"),
        (((100, "degF"), (10, "kelvin")), "error"),
        (((100, "degF"), (10, "degC")), "error"),
        (((100, "degF"), (10, "degF")), "error"),
        (((100, "degF"), (10, "degR")), "error"),
        (((100, "degF"), (10, "delta_degC")), "error"),
        (((100, "degF"), (10, "delta_degF")), "error"),
        (((100, "degR"), (10, "kelvin")), (1000, "degR*kelvin")),
        (((100, "degR"), (10, "degC")), "error"),
        (((100, "degR"), (10, "degF")), "error"),
        (((100, "degR"), (10, "degR")), (1000, "degR**2")),
        (((100, "degR"), (10, "delta_degC")), (1000, "degR*delta_degC")),
        (((100, "degR"), (10, "delta_degF")), (1000, "degR*delta_degF")),
        (((100, "delta_degC"), (10, "kelvin")), (1000, "delta_degC*kelvin")),
        (((100, "delta_degC"), (10, "degC")), "error"),
        (((100, "delta_degC"), (10, "degF")), "error"),
        (((100, "delta_degC"), (10, "degR")), (1000, "delta_degC*degR")),
        (((100, "delta_degC"), (10, "delta_degC")), (1000, "delta_degC**2")),
        (((100, "delta_degC"), (10, "delta_degF")), (1000, "delta_degC*delta_degF")),
        (((100, "delta_degF"), (10, "kelvin")), (1000, "delta_degF*kelvin")),
        (((100, "delta_degF"), (10, "degC")), "error"),
        (((100, "delta_degF"), (10, "degF")), "error"),
        (((100, "delta_degF"), (10, "degR")), (1000, "delta_degF*degR")),
        (((100, "delta_degF"), (10, "delta_degC")), (1000, "delta_degF*delta_degC")),
        (((100, "delta_degF"), (10, "delta_degF")), (1000, "delta_degF**2")),
    ]

    @ParameterizedTestCase.parameterize(("input", "expected_output"), multiplications)
    def test_multiplication(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = False
        qin1, qin2 = input_tuple
        q1, q2 = self.Q_(*qin1), self.Q_(*qin2)
        input_tuple = q1, q2
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.mul, q1, q2)
        else:
            expected = self.Q_(*expected)
            self.assertEqual(op.mul(q1, q2).units, expected.units)
            self.assertQuantityAlmostEqual(op.mul(q1, q2), expected, atol=0.01)

    @helpers.requires_numpy()
    @ParameterizedTestCase.parameterize(("input", "expected_output"), multiplications)
    def test_inplace_multiplication(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = False
        (q1v, q1u), (q2v, q2u) = input_tuple
        # update input tuple with new values to have correct values on failure
        input_tuple = (
            (np.array([q1v] * 2, dtype=np.float), q1u),
            (np.array([q2v] * 2, dtype=np.float), q2u),
        )
        Q_ = self.Q_
        qin1, qin2 = input_tuple
        q1, q2 = Q_(*qin1), Q_(*qin2)
        q1_cp = copy.copy(q1)
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.imul, q1_cp, q2)
        else:
            expected = np.array([expected[0]] * 2, dtype=np.float), expected[1]
            self.assertEqual(op.imul(q1_cp, q2).units, Q_(*expected).units)
            q1_cp = copy.copy(q1)
            self.assertQuantityAlmostEqual(op.imul(q1_cp, q2), Q_(*expected), atol=0.01)

    divisions = [
        (((100, "kelvin"), (10, "kelvin")), (10, "")),
        (((100, "kelvin"), (10, "degC")), "error"),
        (((100, "kelvin"), (10, "degF")), "error"),
        (((100, "kelvin"), (10, "degR")), (10, "kelvin/degR")),
        (((100, "kelvin"), (10, "delta_degC")), (10, "kelvin/delta_degC")),
        (((100, "kelvin"), (10, "delta_degF")), (10, "kelvin/delta_degF")),
        (((100, "degC"), (10, "kelvin")), "error"),
        (((100, "degC"), (10, "degC")), "error"),
        (((100, "degC"), (10, "degF")), "error"),
        (((100, "degC"), (10, "degR")), "error"),
        (((100, "degC"), (10, "delta_degC")), "error"),
        (((100, "degC"), (10, "delta_degF")), "error"),
        (((100, "degF"), (10, "kelvin")), "error"),
        (((100, "degF"), (10, "degC")), "error"),
        (((100, "degF"), (10, "degF")), "error"),
        (((100, "degF"), (10, "degR")), "error"),
        (((100, "degF"), (10, "delta_degC")), "error"),
        (((100, "degF"), (10, "delta_degF")), "error"),
        (((100, "degR"), (10, "kelvin")), (10, "degR/kelvin")),
        (((100, "degR"), (10, "degC")), "error"),
        (((100, "degR"), (10, "degF")), "error"),
        (((100, "degR"), (10, "degR")), (10, "")),
        (((100, "degR"), (10, "delta_degC")), (10, "degR/delta_degC")),
        (((100, "degR"), (10, "delta_degF")), (10, "degR/delta_degF")),
        (((100, "delta_degC"), (10, "kelvin")), (10, "delta_degC/kelvin")),
        (((100, "delta_degC"), (10, "degC")), "error"),
        (((100, "delta_degC"), (10, "degF")), "error"),
        (((100, "delta_degC"), (10, "degR")), (10, "delta_degC/degR")),
        (((100, "delta_degC"), (10, "delta_degC")), (10, "")),
        (((100, "delta_degC"), (10, "delta_degF")), (10, "delta_degC/delta_degF")),
        (((100, "delta_degF"), (10, "kelvin")), (10, "delta_degF/kelvin")),
        (((100, "delta_degF"), (10, "degC")), "error"),
        (((100, "delta_degF"), (10, "degF")), "error"),
        (((100, "delta_degF"), (10, "degR")), (10, "delta_degF/degR")),
        (((100, "delta_degF"), (10, "delta_degC")), (10, "delta_degF/delta_degC")),
        (((100, "delta_degF"), (10, "delta_degF")), (10, "")),
    ]

    @ParameterizedTestCase.parameterize(("input", "expected_output"), divisions)
    def test_truedivision(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = False
        qin1, qin2 = input_tuple
        q1, q2 = self.Q_(*qin1), self.Q_(*qin2)
        input_tuple = q1, q2
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.truediv, q1, q2)
        else:
            expected = self.Q_(*expected)
            self.assertEqual(op.truediv(q1, q2).units, expected.units)
            self.assertQuantityAlmostEqual(op.truediv(q1, q2), expected, atol=0.01)

    @helpers.requires_numpy()
    @ParameterizedTestCase.parameterize(("input", "expected_output"), divisions)
    def test_inplace_truedivision(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = False
        (q1v, q1u), (q2v, q2u) = input_tuple
        # update input tuple with new values to have correct values on failure
        input_tuple = (
            (np.array([q1v] * 2, dtype=np.float), q1u),
            (np.array([q2v] * 2, dtype=np.float), q2u),
        )
        Q_ = self.Q_
        qin1, qin2 = input_tuple
        q1, q2 = Q_(*qin1), Q_(*qin2)
        q1_cp = copy.copy(q1)
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.itruediv, q1_cp, q2)
        else:
            expected = np.array([expected[0]] * 2, dtype=np.float), expected[1]
            self.assertEqual(op.itruediv(q1_cp, q2).units, Q_(*expected).units)
            q1_cp = copy.copy(q1)
            self.assertQuantityAlmostEqual(
                op.itruediv(q1_cp, q2), Q_(*expected), atol=0.01
            )

    multiplications_with_autoconvert_to_baseunit = [
        (((100, "kelvin"), (10, "degC")), (28315.0, "kelvin**2")),
        (((100, "kelvin"), (10, "degF")), (26092.78, "kelvin**2")),
        (((100, "degC"), (10, "kelvin")), (3731.5, "kelvin**2")),
        (((100, "degC"), (10, "degC")), (105657.42, "kelvin**2")),
        (((100, "degC"), (10, "degF")), (97365.20, "kelvin**2")),
        (((100, "degC"), (10, "degR")), (3731.5, "kelvin*degR")),
        (((100, "degC"), (10, "delta_degC")), (3731.5, "kelvin*delta_degC")),
        (((100, "degC"), (10, "delta_degF")), (3731.5, "kelvin*delta_degF")),
        (((100, "degF"), (10, "kelvin")), (3109.28, "kelvin**2")),
        (((100, "degF"), (10, "degC")), (88039.20, "kelvin**2")),
        (((100, "degF"), (10, "degF")), (81129.69, "kelvin**2")),
        (((100, "degF"), (10, "degR")), (3109.28, "kelvin*degR")),
        (((100, "degF"), (10, "delta_degC")), (3109.28, "kelvin*delta_degC")),
        (((100, "degF"), (10, "delta_degF")), (3109.28, "kelvin*delta_degF")),
        (((100, "degR"), (10, "degC")), (28315.0, "degR*kelvin")),
        (((100, "degR"), (10, "degF")), (26092.78, "degR*kelvin")),
        (((100, "delta_degC"), (10, "degC")), (28315.0, "delta_degC*kelvin")),
        (((100, "delta_degC"), (10, "degF")), (26092.78, "delta_degC*kelvin")),
        (((100, "delta_degF"), (10, "degC")), (28315.0, "delta_degF*kelvin")),
        (((100, "delta_degF"), (10, "degF")), (26092.78, "delta_degF*kelvin")),
    ]

    @ParameterizedTestCase.parameterize(
        ("input", "expected_output"), multiplications_with_autoconvert_to_baseunit
    )
    def test_multiplication_with_autoconvert(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = True
        qin1, qin2 = input_tuple
        q1, q2 = self.Q_(*qin1), self.Q_(*qin2)
        input_tuple = q1, q2
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.mul, q1, q2)
        else:
            expected = self.Q_(*expected)
            self.assertEqual(op.mul(q1, q2).units, expected.units)
            self.assertQuantityAlmostEqual(op.mul(q1, q2), expected, atol=0.01)

    @helpers.requires_numpy()
    @ParameterizedTestCase.parameterize(
        ("input", "expected_output"), multiplications_with_autoconvert_to_baseunit
    )
    def test_inplace_multiplication_with_autoconvert(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = True
        (q1v, q1u), (q2v, q2u) = input_tuple
        # update input tuple with new values to have correct values on failure
        input_tuple = (
            (np.array([q1v] * 2, dtype=np.float), q1u),
            (np.array([q2v] * 2, dtype=np.float), q2u),
        )
        Q_ = self.Q_
        qin1, qin2 = input_tuple
        q1, q2 = Q_(*qin1), Q_(*qin2)
        q1_cp = copy.copy(q1)
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.imul, q1_cp, q2)
        else:
            expected = np.array([expected[0]] * 2, dtype=np.float), expected[1]
            self.assertEqual(op.imul(q1_cp, q2).units, Q_(*expected).units)
            q1_cp = copy.copy(q1)
            self.assertQuantityAlmostEqual(op.imul(q1_cp, q2), Q_(*expected), atol=0.01)

    multiplications_with_scalar = [
        (((10, "kelvin"), 2), (20.0, "kelvin")),
        (((10, "kelvin**2"), 2), (20.0, "kelvin**2")),
        (((10, "degC"), 2), (20.0, "degC")),
        (((10, "1/degC"), 2), "error"),
        (((10, "degC**0.5"), 2), "error"),
        (((10, "degC**2"), 2), "error"),
        (((10, "degC**-2"), 2), "error"),
    ]

    @ParameterizedTestCase.parameterize(
        ("input", "expected_output"), multiplications_with_scalar
    )
    def test_multiplication_with_scalar(self, input_tuple, expected):
        self.ureg.default_as_delta = False
        in1, in2 = input_tuple
        if type(in1) is tuple:
            in1, in2 = self.Q_(*in1), in2
        else:
            in1, in2 = in1, self.Q_(*in2)
        input_tuple = in1, in2  # update input_tuple for better tracebacks
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.mul, in1, in2)
        else:
            expected = self.Q_(*expected)
            self.assertEqual(op.mul(in1, in2).units, expected.units)
            self.assertQuantityAlmostEqual(op.mul(in1, in2), expected, atol=0.01)

    divisions_with_scalar = [  # without / with autoconvert to base unit
        (((10, "kelvin"), 2), [(5.0, "kelvin"), (5.0, "kelvin")]),
        (((10, "kelvin**2"), 2), [(5.0, "kelvin**2"), (5.0, "kelvin**2")]),
        (((10, "degC"), 2), ["error", "error"]),
        (((10, "degC**2"), 2), ["error", "error"]),
        (((10, "degC**-2"), 2), ["error", "error"]),
        ((2, (10, "kelvin")), [(0.2, "1/kelvin"), (0.2, "1/kelvin")]),
        ((2, (10, "degC")), ["error", (2 / 283.15, "1/kelvin")]),
        ((2, (10, "degC**2")), ["error", "error"]),
        ((2, (10, "degC**-2")), ["error", "error"]),
    ]

    @ParameterizedTestCase.parameterize(
        ("input", "expected_output"), divisions_with_scalar
    )
    def test_division_with_scalar(self, input_tuple, expected):
        self.ureg.default_as_delta = False
        in1, in2 = input_tuple
        if type(in1) is tuple:
            in1, in2 = self.Q_(*in1), in2
        else:
            in1, in2 = in1, self.Q_(*in2)
        input_tuple = in1, in2  # update input_tuple for better tracebacks
        expected_copy = expected[:]
        for i, mode in enumerate([False, True]):
            self.ureg.autoconvert_offset_to_baseunit = mode
            if expected_copy[i] == "error":
                self.assertRaises(OffsetUnitCalculusError, op.truediv, in1, in2)
            else:
                expected = self.Q_(*expected_copy[i])
                self.assertEqual(op.truediv(in1, in2).units, expected.units)
                self.assertQuantityAlmostEqual(op.truediv(in1, in2), expected)

    exponentiation = [  # resuls without / with autoconvert
        (((10, "degC"), 1), [(10, "degC"), (10, "degC")]),
        (((10, "degC"), 0.5), ["error", (283.15 ** 0.5, "kelvin**0.5")]),
        (((10, "degC"), 0), [(1.0, ""), (1.0, "")]),
        (((10, "degC"), -1), ["error", (1 / (10 + 273.15), "kelvin**-1")]),
        (((10, "degC"), -2), ["error", (1 / (10 + 273.15) ** 2.0, "kelvin**-2")]),
        (((0, "degC"), -2), ["error", (1 / (273.15) ** 2, "kelvin**-2")]),
        (((10, "degC"), (2, "")), ["error", ((283.15) ** 2, "kelvin**2")]),
        (((10, "degC"), (10, "degK")), ["error", "error"]),
        (((10, "kelvin"), (2, "")), [(100.0, "kelvin**2"), (100.0, "kelvin**2")]),
        ((2, (2, "kelvin")), ["error", "error"]),
        ((2, (500.0, "millikelvin/kelvin")), [2 ** 0.5, 2 ** 0.5]),
        ((2, (0.5, "kelvin/kelvin")), [2 ** 0.5, 2 ** 0.5]),
        (
            ((10, "degC"), (500.0, "millikelvin/kelvin")),
            ["error", (283.15 ** 0.5, "kelvin**0.5")],
        ),
    ]

    @ParameterizedTestCase.parameterize(("input", "expected_output"), exponentiation)
    def test_exponentiation(self, input_tuple, expected):
        self.ureg.default_as_delta = False
        in1, in2 = input_tuple
        if type(in1) is tuple and type(in2) is tuple:
            in1, in2 = self.Q_(*in1), self.Q_(*in2)
        elif not type(in1) is tuple and type(in2) is tuple:
            in2 = self.Q_(*in2)
        else:
            in1 = self.Q_(*in1)
        input_tuple = in1, in2
        expected_copy = expected[:]
        for i, mode in enumerate([False, True]):
            self.ureg.autoconvert_offset_to_baseunit = mode
            if expected_copy[i] == "error":
                self.assertRaises(
                    (OffsetUnitCalculusError, DimensionalityError), op.pow, in1, in2
                )
            else:
                if type(expected_copy[i]) is tuple:
                    expected = self.Q_(*expected_copy[i])
                    self.assertEqual(op.pow(in1, in2).units, expected.units)
                else:
                    expected = expected_copy[i]
                self.assertQuantityAlmostEqual(op.pow(in1, in2), expected)

    @helpers.requires_numpy()
    @ParameterizedTestCase.parameterize(("input", "expected_output"), exponentiation)
    def test_inplace_exponentiation(self, input_tuple, expected):
        self.ureg.default_as_delta = False
        in1, in2 = input_tuple
        if type(in1) is tuple and type(in2) is tuple:
            (q1v, q1u), (q2v, q2u) = in1, in2
            in1 = self.Q_(*(np.array([q1v] * 2, dtype=np.float), q1u))
            in2 = self.Q_(q2v, q2u)
        elif not type(in1) is tuple and type(in2) is tuple:
            in2 = self.Q_(*in2)
        else:
            in1 = self.Q_(*in1)

        input_tuple = in1, in2

        expected_copy = expected[:]
        for i, mode in enumerate([False, True]):
            self.ureg.autoconvert_offset_to_baseunit = mode
            in1_cp = copy.copy(in1)
            if expected_copy[i] == "error":
                self.assertRaises(
                    (OffsetUnitCalculusError, DimensionalityError), op.ipow, in1_cp, in2
                )
            else:
                if type(expected_copy[i]) is tuple:
                    expected = self.Q_(
                        np.array([expected_copy[i][0]] * 2, dtype=np.float),
                        expected_copy[i][1],
                    )
                    self.assertEqual(op.ipow(in1_cp, in2).units, expected.units)
                else:
                    expected = np.array([expected_copy[i]] * 2, dtype=np.float)

                in1_cp = copy.copy(in1)
                self.assertQuantityAlmostEqual(op.ipow(in1_cp, in2), expected)

    # matmul is only a ufunc since 1.16
    @helpers.requires_numpy_at_least("1.16")
    def test_matmul_with_numpy(self):
        A = [[1, 2], [3, 4]] * self.ureg.m
        B = np.array([[0, -1], [-1, 0]])
        b = [[1], [0]] * self.ureg.m
        self.assertQuantityEqual(A @ B, [[-2, -1], [-4, -3]] * self.ureg.m)
        self.assertQuantityEqual(A @ b, [[1], [3]] * self.ureg.m ** 2)
        self.assertQuantityEqual(B @ b, [[0], [-1]] * self.ureg.m)


class TestDimensionReduction(QuantityTestCase):
    def _calc_mass(self, ureg):
        density = 3 * ureg.g / ureg.L
        volume = 32 * ureg.milliliter
        return density * volume

    def _icalc_mass(self, ureg):
        res = ureg.Quantity(3.0, "gram/liter")
        res *= ureg.Quantity(32.0, "milliliter")
        return res

    def test_mul_and_div_reduction(self):
        ureg = UnitRegistry(auto_reduce_dimensions=True)
        mass = self._calc_mass(ureg)
        self.assertEqual(mass.units, ureg.g)
        ureg = UnitRegistry(auto_reduce_dimensions=False)
        mass = self._calc_mass(ureg)
        self.assertEqual(mass.units, ureg.g / ureg.L * ureg.milliliter)

    @helpers.requires_numpy()
    def test_imul_and_div_reduction(self):
        ureg = UnitRegistry(auto_reduce_dimensions=True, force_ndarray=True)
        mass = self._icalc_mass(ureg)
        self.assertEqual(mass.units, ureg.g)
        ureg = UnitRegistry(auto_reduce_dimensions=False, force_ndarray=True)
        mass = self._icalc_mass(ureg)
        self.assertEqual(mass.units, ureg.g / ureg.L * ureg.milliliter)

    def test_reduction_to_dimensionless(self):
        ureg = UnitRegistry(auto_reduce_dimensions=True)
        x = (10 * ureg.feet) / (3 * ureg.inches)
        self.assertEqual(x.units, UnitsContainer({}))
        ureg = UnitRegistry(auto_reduce_dimensions=False)
        x = (10 * ureg.feet) / (3 * ureg.inches)
        self.assertEqual(x.units, ureg.feet / ureg.inches)

    def test_nocoerce_creation(self):
        ureg = UnitRegistry(auto_reduce_dimensions=True)
        x = 1 * ureg.foot
        self.assertEqual(x.units, ureg.foot)


class TestTimedelta(QuantityTestCase):
    def test_add_sub(self):
        d = datetime.datetime(year=1968, month=1, day=10, hour=3, minute=42, second=24)
        after = d + 3 * self.ureg.second
        self.assertEqual(d + datetime.timedelta(seconds=3), after)
        after = 3 * self.ureg.second + d
        self.assertEqual(d + datetime.timedelta(seconds=3), after)
        after = d - 3 * self.ureg.second
        self.assertEqual(d - datetime.timedelta(seconds=3), after)
        with self.assertRaises(DimensionalityError):
            3 * self.ureg.second - d

    def test_iadd_isub(self):
        d = datetime.datetime(year=1968, month=1, day=10, hour=3, minute=42, second=24)
        after = copy.copy(d)
        after += 3 * self.ureg.second
        self.assertEqual(d + datetime.timedelta(seconds=3), after)
        after = 3 * self.ureg.second
        after += d
        self.assertEqual(d + datetime.timedelta(seconds=3), after)
        after = copy.copy(d)
        after -= 3 * self.ureg.second
        self.assertEqual(d - datetime.timedelta(seconds=3), after)
        after = 3 * self.ureg.second
        with self.assertRaises(DimensionalityError):
            after -= d


class TestCompareNeutral(QuantityTestCase):
    """Test comparisons against non-Quantity zero or NaN values for for
    non-dimensionless quantities
    """

    def test_equal_zero(self):
        self.ureg.autoconvert_offset_to_baseunit = False
        self.assertTrue(self.Q_(0, "J") == 0)
        self.assertFalse(self.Q_(0, "J") == self.Q_(0, ""))
        self.assertFalse(self.Q_(5, "J") == 0)

    def test_equal_nan(self):
        # nan == nan returns False
        self.ureg.autoconvert_offset_to_baseunit = False
        self.assertFalse(self.Q_(math.nan, "J") == 0)
        self.assertFalse(self.Q_(math.nan, "J") == math.nan)
        self.assertFalse(self.Q_(math.nan, "J") == self.Q_(math.nan, ""))
        self.assertFalse(self.Q_(5, "J") == math.nan)

    @helpers.requires_numpy()
    def test_equal_zero_nan_NP(self):
        self.ureg.autoconvert_offset_to_baseunit = False
        aeq = np.testing.assert_array_equal
        aeq(self.Q_(0, "J") == np.array([0, np.nan]), np.array([True, False]))
        aeq(self.Q_(5, "J") == np.array([0, np.nan]), np.array([False, False]))
        aeq(
            self.Q_([0, 1, 2], "J") == np.array([0, 0, np.nan]),
            np.asarray([True, False, False]),
        )
        self.assertFalse(self.Q_(np.arange(4), "J") == np.zeros(3))

    def test_offset_equal_zero(self):
        ureg = self.ureg
        ureg.autoconvert_offset_to_baseunit = False
        q0 = ureg.Quantity(-273.15, "degC")
        q1 = ureg.Quantity(0, "degC")
        q2 = ureg.Quantity(5, "degC")
        self.assertRaises(OffsetUnitCalculusError, q0.__eq__, 0)
        self.assertRaises(OffsetUnitCalculusError, q1.__eq__, 0)
        self.assertRaises(OffsetUnitCalculusError, q2.__eq__, 0)
        self.assertFalse(q0 == ureg.Quantity(0, ""))

    def test_offset_autoconvert_equal_zero(self):
        ureg = self.ureg
        ureg.autoconvert_offset_to_baseunit = True
        q0 = ureg.Quantity(-273.15, "degC")
        q1 = ureg.Quantity(0, "degC")
        q2 = ureg.Quantity(5, "degC")
        self.assertTrue(q0 == 0)
        self.assertFalse(q1 == 0)
        self.assertFalse(q2 == 0)
        self.assertFalse(q0 == ureg.Quantity(0, ""))

    def test_gt_zero(self):
        self.ureg.autoconvert_offset_to_baseunit = False
        q0 = self.Q_(0, "J")
        q0m = self.Q_(0, "m")
        q0less = self.Q_(0, "")
        qpos = self.Q_(5, "J")
        qneg = self.Q_(-5, "J")
        self.assertTrue(qpos > q0)
        self.assertTrue(qpos > 0)
        self.assertFalse(qneg > 0)
        with self.assertRaises(DimensionalityError):
            qpos > q0less
        with self.assertRaises(DimensionalityError):
            qpos > q0m

    def test_gt_nan(self):
        self.ureg.autoconvert_offset_to_baseunit = False
        qn = self.Q_(math.nan, "J")
        qnm = self.Q_(math.nan, "m")
        qnless = self.Q_(math.nan, "")
        qpos = self.Q_(5, "J")
        self.assertFalse(qpos > qn)
        self.assertFalse(qpos > math.nan)
        with self.assertRaises(DimensionalityError):
            qpos > qnless
        with self.assertRaises(DimensionalityError):
            qpos > qnm

    @helpers.requires_numpy()
    def test_gt_zero_nan_NP(self):
        self.ureg.autoconvert_offset_to_baseunit = False
        qpos = self.Q_(5, "J")
        qneg = self.Q_(-5, "J")
        aeq = np.testing.assert_array_equal
        aeq(qpos > np.array([0, np.nan]), np.asarray([True, False]))
        aeq(qneg > np.array([0, np.nan]), np.asarray([False, False]))
        aeq(
            self.Q_(np.arange(-2, 3), "J") > np.array([np.nan, 0, 0, 0, np.nan]),
            np.asarray([False, False, False, True, False]),
        )
        with self.assertRaises(ValueError):
            self.Q_(np.arange(-1, 2), "J") > np.zeros(4)

    def test_offset_gt_zero(self):
        ureg = self.ureg
        ureg.autoconvert_offset_to_baseunit = False
        q0 = ureg.Quantity(-273.15, "degC")
        q1 = ureg.Quantity(0, "degC")
        q2 = ureg.Quantity(5, "degC")
        self.assertRaises(OffsetUnitCalculusError, q0.__gt__, 0)
        self.assertRaises(OffsetUnitCalculusError, q1.__gt__, 0)
        self.assertRaises(OffsetUnitCalculusError, q2.__gt__, 0)
        self.assertRaises(DimensionalityError, q1.__gt__, ureg.Quantity(0, ""))

    def test_offset_autoconvert_gt_zero(self):
        ureg = self.ureg
        ureg.autoconvert_offset_to_baseunit = True
        q0 = ureg.Quantity(-273.15, "degC")
        q1 = ureg.Quantity(0, "degC")
        q2 = ureg.Quantity(5, "degC")
        self.assertFalse(q0 > 0)
        self.assertTrue(q1 > 0)
        self.assertTrue(q2 > 0)
        self.assertRaises(DimensionalityError, q1.__gt__, ureg.Quantity(0, ""))
