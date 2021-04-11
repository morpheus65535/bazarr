import copy
import math
import pprint
import unittest

import pytest

from pint import Context, DimensionalityError, UnitRegistry, get_application_registry
from pint.compat import np
from pint.testsuite import QuantityTestCase, helpers
from pint.unit import UnitsContainer
from pint.util import ParserHelper

ureg = UnitRegistry()


class TestIssues(QuantityTestCase):

    FORCE_NDARRAY = False

    def setup(self):
        self.ureg.autoconvert_offset_to_baseunit = False

    @unittest.expectedFailure
    def test_issue25(self):
        x = ParserHelper.from_string("10 %")
        self.assertEqual(x, ParserHelper(10, {"%": 1}))
        x = ParserHelper.from_string("10 ‰")
        self.assertEqual(x, ParserHelper(10, {"‰": 1}))
        ureg.define("percent = [fraction]; offset: 0 = %")
        ureg.define("permille = percent / 10 = ‰")
        x = ureg.parse_expression("10 %")
        self.assertEqual(x, ureg.Quantity(10, {"%": 1}))
        y = ureg.parse_expression("10 ‰")
        self.assertEqual(y, ureg.Quantity(10, {"‰": 1}))
        self.assertEqual(x.to("‰"), ureg.Quantity(1, {"‰": 1}))

    def test_issue29(self):
        t = 4 * ureg("mW")
        self.assertEqual(t.magnitude, 4)
        self.assertEqual(t._units, UnitsContainer(milliwatt=1))
        self.assertEqual(t.to("joule / second"), 4e-3 * ureg("W"))

    @unittest.expectedFailure
    @helpers.requires_numpy()
    def test_issue37(self):
        x = np.ma.masked_array([1, 2, 3], mask=[True, True, False])
        q = ureg.meter * x
        self.assertIsInstance(q, ureg.Quantity)
        np.testing.assert_array_equal(q.magnitude, x)
        self.assertEqual(q.units, ureg.meter.units)
        q = x * ureg.meter
        self.assertIsInstance(q, ureg.Quantity)
        np.testing.assert_array_equal(q.magnitude, x)
        self.assertEqual(q.units, ureg.meter.units)

        m = np.ma.masked_array(2 * np.ones(3, 3))
        qq = q * m
        self.assertIsInstance(qq, ureg.Quantity)
        np.testing.assert_array_equal(qq.magnitude, x * m)
        self.assertEqual(qq.units, ureg.meter.units)
        qq = m * q
        self.assertIsInstance(qq, ureg.Quantity)
        np.testing.assert_array_equal(qq.magnitude, x * m)
        self.assertEqual(qq.units, ureg.meter.units)

    @unittest.expectedFailure
    @helpers.requires_numpy()
    def test_issue39(self):
        x = np.matrix([[1, 2, 3], [1, 2, 3], [1, 2, 3]])
        q = ureg.meter * x
        self.assertIsInstance(q, ureg.Quantity)
        np.testing.assert_array_equal(q.magnitude, x)
        self.assertEqual(q.units, ureg.meter.units)
        q = x * ureg.meter
        self.assertIsInstance(q, ureg.Quantity)
        np.testing.assert_array_equal(q.magnitude, x)
        self.assertEqual(q.units, ureg.meter.units)

        m = np.matrix(2 * np.ones(3, 3))
        qq = q * m
        self.assertIsInstance(qq, ureg.Quantity)
        np.testing.assert_array_equal(qq.magnitude, x * m)
        self.assertEqual(qq.units, ureg.meter.units)
        qq = m * q
        self.assertIsInstance(qq, ureg.Quantity)
        np.testing.assert_array_equal(qq.magnitude, x * m)
        self.assertEqual(qq.units, ureg.meter.units)

    @helpers.requires_numpy()
    def test_issue44(self):
        x = 4.0 * ureg.dimensionless
        np.sqrt(x)
        self.assertQuantityAlmostEqual(
            np.sqrt([4.0] * ureg.dimensionless), [2.0] * ureg.dimensionless
        )
        self.assertQuantityAlmostEqual(
            np.sqrt(4.0 * ureg.dimensionless), 2.0 * ureg.dimensionless
        )

    def test_issue45(self):
        import math

        self.assertAlmostEqual(math.sqrt(4 * ureg.m / ureg.cm), math.sqrt(4 * 100))
        self.assertAlmostEqual(float(ureg.V / ureg.mV), 1000.0)

    @helpers.requires_numpy()
    def test_issue45b(self):
        self.assertAlmostEqual(
            np.sin([np.pi / 2] * ureg.m / ureg.m),
            np.sin([np.pi / 2] * ureg.dimensionless),
        )
        self.assertAlmostEqual(
            np.sin([np.pi / 2] * ureg.cm / ureg.m),
            np.sin([np.pi / 2] * ureg.dimensionless * 0.01),
        )

    def test_issue50(self):
        Q_ = ureg.Quantity
        self.assertEqual(Q_(100), 100 * ureg.dimensionless)
        self.assertEqual(Q_("100"), 100 * ureg.dimensionless)

    def test_issue52(self):
        u1 = UnitRegistry()
        u2 = UnitRegistry()
        q1 = 1 * u1.meter
        q2 = 1 * u2.meter
        import operator as op

        for fun in (
            op.add,
            op.iadd,
            op.sub,
            op.isub,
            op.mul,
            op.imul,
            op.floordiv,
            op.ifloordiv,
            op.truediv,
            op.itruediv,
        ):
            self.assertRaises(ValueError, fun, q1, q2)

    def test_issue54(self):
        self.assertEqual((1 * ureg.km / ureg.m + 1).magnitude, 1001)

    def test_issue54_related(self):
        self.assertEqual(ureg.km / ureg.m, 1000)
        self.assertEqual(1000, ureg.km / ureg.m)
        self.assertLess(900, ureg.km / ureg.m)
        self.assertGreater(1100, ureg.km / ureg.m)

    def test_issue61(self):
        Q_ = ureg.Quantity
        for value in ({}, {"a": 3}, None):
            self.assertRaises(TypeError, Q_, value)
            self.assertRaises(TypeError, Q_, value, "meter")
        self.assertRaises(ValueError, Q_, "", "meter")
        self.assertRaises(ValueError, Q_, "")

    @helpers.requires_not_numpy()
    def test_issue61_notNP(self):
        Q_ = ureg.Quantity
        for value in ([1, 2, 3], (1, 2, 3)):
            self.assertRaises(TypeError, Q_, value)
            self.assertRaises(TypeError, Q_, value, "meter")

    def test_issue62(self):
        m = ureg("m**0.5")
        self.assertEqual(str(m.units), "meter ** 0.5")

    def test_issue66(self):
        self.assertEqual(
            ureg.get_dimensionality(UnitsContainer({"[temperature]": 1})),
            UnitsContainer({"[temperature]": 1}),
        )
        self.assertEqual(
            ureg.get_dimensionality(ureg.kelvin), UnitsContainer({"[temperature]": 1})
        )
        self.assertEqual(
            ureg.get_dimensionality(ureg.degC), UnitsContainer({"[temperature]": 1})
        )

    def test_issue66b(self):
        self.assertEqual(
            ureg.get_base_units(ureg.kelvin),
            (1.0, ureg.Unit(UnitsContainer({"kelvin": 1}))),
        )
        self.assertEqual(
            ureg.get_base_units(ureg.degC),
            (1.0, ureg.Unit(UnitsContainer({"kelvin": 1}))),
        )

    def test_issue69(self):
        q = ureg("m").to(ureg("in"))
        self.assertEqual(q, ureg("m").to("in"))

    @helpers.requires_numpy()
    def test_issue74(self):
        v1 = np.asarray([1.0, 2.0, 3.0])
        v2 = np.asarray([3.0, 2.0, 1.0])
        q1 = v1 * ureg.ms
        q2 = v2 * ureg.ms

        np.testing.assert_array_equal(q1 < q2, v1 < v2)
        np.testing.assert_array_equal(q1 > q2, v1 > v2)

        np.testing.assert_array_equal(q1 <= q2, v1 <= v2)
        np.testing.assert_array_equal(q1 >= q2, v1 >= v2)

        q2s = np.asarray([0.003, 0.002, 0.001]) * ureg.s
        v2s = q2s.to("ms").magnitude

        np.testing.assert_array_equal(q1 < q2s, v1 < v2s)
        np.testing.assert_array_equal(q1 > q2s, v1 > v2s)

        np.testing.assert_array_equal(q1 <= q2s, v1 <= v2s)
        np.testing.assert_array_equal(q1 >= q2s, v1 >= v2s)

    @helpers.requires_numpy()
    def test_issue75(self):
        v1 = np.asarray([1.0, 2.0, 3.0])
        v2 = np.asarray([3.0, 2.0, 1.0])
        q1 = v1 * ureg.ms
        q2 = v2 * ureg.ms

        np.testing.assert_array_equal(q1 == q2, v1 == v2)
        np.testing.assert_array_equal(q1 != q2, v1 != v2)

        q2s = np.asarray([0.003, 0.002, 0.001]) * ureg.s
        v2s = q2s.to("ms").magnitude

        np.testing.assert_array_equal(q1 == q2s, v1 == v2s)
        np.testing.assert_array_equal(q1 != q2s, v1 != v2s)

    @helpers.requires_uncertainties()
    def test_issue77(self):
        acc = (5.0 * ureg("m/s/s")).plus_minus(0.25)
        tim = (37.0 * ureg("s")).plus_minus(0.16)
        dis = acc * tim ** 2 / 2
        self.assertEqual(dis.value, acc.value * tim.value ** 2 / 2)

    def test_issue85(self):

        T = 4.0 * ureg.kelvin
        m = 1.0 * ureg.amu
        va = 2.0 * ureg.k * T / m

        va.to_base_units()

        boltmk = 1.380649e-23 * ureg.J / ureg.K
        vb = 2.0 * boltmk * T / m

        self.assertQuantityAlmostEqual(va.to_base_units(), vb.to_base_units())

    def test_issue86(self):
        ureg = self.ureg
        ureg.autoconvert_offset_to_baseunit = True

        def parts(q):
            return q.magnitude, q.units

        q1 = 10.0 * ureg.degC
        q2 = 10.0 * ureg.kelvin

        k1 = q1.to_base_units()

        q3 = 3.0 * ureg.meter

        q1m, q1u = parts(q1)
        q2m, q2u = parts(q2)
        q3m, q3u = parts(q3)

        k1m, k1u = parts(k1)

        self.assertEqual(parts(q2 * q3), (q2m * q3m, q2u * q3u))
        self.assertEqual(parts(q2 / q3), (q2m / q3m, q2u / q3u))
        self.assertEqual(parts(q3 * q2), (q3m * q2m, q3u * q2u))
        self.assertEqual(parts(q3 / q2), (q3m / q2m, q3u / q2u))
        self.assertEqual(parts(q2 ** 1), (q2m ** 1, q2u ** 1))
        self.assertEqual(parts(q2 ** -1), (q2m ** -1, q2u ** -1))
        self.assertEqual(parts(q2 ** 2), (q2m ** 2, q2u ** 2))
        self.assertEqual(parts(q2 ** -2), (q2m ** -2, q2u ** -2))

        self.assertEqual(parts(q1 * q3), (k1m * q3m, k1u * q3u))
        self.assertEqual(parts(q1 / q3), (k1m / q3m, k1u / q3u))
        self.assertEqual(parts(q3 * q1), (q3m * k1m, q3u * k1u))
        self.assertEqual(parts(q3 / q1), (q3m / k1m, q3u / k1u))
        self.assertEqual(parts(q1 ** -1), (k1m ** -1, k1u ** -1))
        self.assertEqual(parts(q1 ** 2), (k1m ** 2, k1u ** 2))
        self.assertEqual(parts(q1 ** -2), (k1m ** -2, k1u ** -2))

    def test_issues86b(self):
        ureg = self.ureg

        T1 = 200.0 * ureg.degC
        T2 = T1.to(ureg.kelvin)
        m = 132.9054519 * ureg.amu
        v1 = 2 * ureg.k * T1 / m
        v2 = 2 * ureg.k * T2 / m

        self.assertQuantityAlmostEqual(v1, v2)
        self.assertQuantityAlmostEqual(v1, v2.to_base_units())
        self.assertQuantityAlmostEqual(v1.to_base_units(), v2)
        self.assertQuantityAlmostEqual(v1.to_base_units(), v2.to_base_units())

    @unittest.expectedFailure
    def test_issue86c(self):
        ureg = self.ureg
        ureg.autoconvert_offset_to_baseunit = True
        T = ureg.degC
        T = 100.0 * T
        self.assertQuantityAlmostEqual(ureg.k * 2 * T, ureg.k * (2 * T))

    def test_issue93(self):
        x = 5 * ureg.meter
        self.assertIsInstance(x.magnitude, int)
        y = 0.1 * ureg.meter
        self.assertIsInstance(y.magnitude, float)
        z = 5 * ureg.meter
        self.assertIsInstance(z.magnitude, int)
        z += y
        self.assertIsInstance(z.magnitude, float)

        self.assertQuantityAlmostEqual(x + y, 5.1 * ureg.meter)
        self.assertQuantityAlmostEqual(z, 5.1 * ureg.meter)

    def test_issue104(self):

        x = [ureg("1 meter"), ureg("1 meter"), ureg("1 meter")]
        y = [ureg("1 meter")] * 3

        def summer(values):
            if not values:
                return 0
            total = values[0]
            for v in values[1:]:
                total += v

            return total

        self.assertQuantityAlmostEqual(summer(x), ureg.Quantity(3, "meter"))
        self.assertQuantityAlmostEqual(x[0], ureg.Quantity(1, "meter"))
        self.assertQuantityAlmostEqual(summer(y), ureg.Quantity(3, "meter"))
        self.assertQuantityAlmostEqual(y[0], ureg.Quantity(1, "meter"))

    def test_issue105(self):

        func = ureg.parse_unit_name
        val = list(func("meter"))
        self.assertEqual(list(func("METER")), [])
        self.assertEqual(val, list(func("METER", False)))

        for func in (ureg.get_name, ureg.parse_expression):
            val = func("meter")
            with self.assertRaises(AttributeError):
                func("METER")
            self.assertEqual(val, func("METER", False))

    @helpers.requires_numpy()
    def test_issue127(self):
        q = [1.0, 2.0, 3.0, 4.0] * self.ureg.meter
        q[0] = np.nan
        self.assertNotEqual(q[0], 1.0)
        self.assertTrue(math.isnan(q[0].magnitude))
        q[1] = float("NaN")
        self.assertNotEqual(q[1], 2.0)
        self.assertTrue(math.isnan(q[1].magnitude))

    def test_issue170(self):
        Q_ = UnitRegistry().Quantity
        q = Q_("1 kHz") / Q_("100 Hz")
        iq = int(q)
        self.assertEqual(iq, 10)
        self.assertIsInstance(iq, int)

    def test_angstrom_creation(self):
        ureg.Quantity(2, "Å")

    def test_alternative_angstrom_definition(self):
        ureg.Quantity(2, "\u212B")

    def test_micro_creation(self):
        ureg.Quantity(2, "µm")

    @helpers.requires_numpy()
    def test_issue171_real_imag(self):
        qr = [1.0, 2.0, 3.0, 4.0] * self.ureg.meter
        qi = [4.0, 3.0, 2.0, 1.0] * self.ureg.meter
        q = qr + 1j * qi
        self.assertQuantityEqual(q.real, qr)
        self.assertQuantityEqual(q.imag, qi)

    @helpers.requires_numpy()
    def test_issue171_T(self):
        a = np.asarray([[1.0, 2.0, 3.0, 4.0], [4.0, 3.0, 2.0, 1.0]])
        q1 = a * self.ureg.meter
        q2 = a.T * self.ureg.meter
        self.assertQuantityEqual(q1.T, q2)

    @helpers.requires_numpy()
    def test_issue250(self):
        a = self.ureg.V
        b = self.ureg.mV
        self.assertEqual(np.float16(a / b), 1000.0)
        self.assertEqual(np.float32(a / b), 1000.0)
        self.assertEqual(np.float64(a / b), 1000.0)
        if "float128" in dir(np):
            self.assertEqual(np.float128(a / b), 1000.0)

    def test_issue252(self):
        ur = UnitRegistry()
        q = ur("3 F")
        t = copy.deepcopy(q)
        u = t.to(ur.mF)
        self.assertQuantityEqual(q.to(ur.mF), u)

    def test_issue323(self):
        from fractions import Fraction as F

        self.assertEqual((self.Q_(F(2, 3), "s")).to("ms"), self.Q_(F(2000, 3), "ms"))
        self.assertEqual((self.Q_(F(2, 3), "m")).to("km"), self.Q_(F(1, 1500), "km"))

    def test_issue339(self):
        q1 = self.ureg("")
        self.assertEqual(q1.magnitude, 1)
        self.assertEqual(q1.units, self.ureg.dimensionless)
        q2 = self.ureg("1 dimensionless")
        self.assertEqual(q1, q2)

    def test_issue354_356_370(self):
        self.assertEqual(
            "{:~}".format(1 * self.ureg.second / self.ureg.millisecond), "1.0 s / ms"
        )
        self.assertEqual("{:~}".format(1 * self.ureg.count), "1 count")
        self.assertEqual("{:~}".format(1 * self.ureg("MiB")), "1 MiB")

    def test_issue468(self):
        @ureg.wraps(("kg"), "meter")
        def f(x):
            return x

        x = ureg.Quantity(1.0, "meter")
        y = f(x)
        z = x * y
        self.assertEqual(z, ureg.Quantity(1.0, "meter * kilogram"))

    @helpers.requires_numpy()
    def test_issue482(self):
        q = self.ureg.Quantity(1, self.ureg.dimensionless)
        qe = np.exp(q)
        self.assertIsInstance(qe, self.ureg.Quantity)

    @helpers.requires_numpy()
    def test_issue483(self):
        ureg = self.ureg
        a = np.asarray([1, 2, 3])
        q = [1, 2, 3] * ureg.dimensionless
        p = (q ** q).m
        np.testing.assert_array_equal(p, a ** a)

    def test_issue507(self):
        # leading underscore in unit works with numbers
        ureg.define("_100km = 100 * kilometer")
        battery_ec = 16 * ureg.kWh / ureg._100km  # noqa: F841
        # ... but not with text
        ureg.define("_home = 4700 * kWh / year")
        with self.assertRaises(AttributeError):
            home_elec_power = 1 * ureg._home  # noqa: F841
        # ... or with *only* underscores
        ureg.define("_ = 45 * km")
        with self.assertRaises(AttributeError):
            one_blank = 1 * ureg._  # noqa: F841

    def test_issue523(self):
        src, dst = UnitsContainer({"meter": 1}), UnitsContainer({"degF": 1})
        value = 10.0
        convert = self.ureg.convert
        self.assertRaises(DimensionalityError, convert, value, src, dst)
        self.assertRaises(DimensionalityError, convert, value, dst, src)

    def test_issue532(self):
        ureg = self.ureg

        @ureg.check(ureg(""))
        def f(x):
            return 2 * x

        self.assertEqual(f(ureg.Quantity(1, "")), 2)
        self.assertRaises(DimensionalityError, f, ureg.Quantity(1, "m"))

    def test_issue625a(self):
        Q_ = ureg.Quantity
        from math import sqrt

        @ureg.wraps(ureg.second, (ureg.meters, ureg.meters / ureg.second ** 2))
        def calculate_time_to_fall(height, gravity=Q_(9.8, "m/s^2")):
            """Calculate time to fall from a height h with a default gravity.

            By default, the gravity is assumed to be earth gravity,
            but it can be modified.

            d = .5 * g * t**2
            t = sqrt(2 * d / g)

            Parameters
            ----------
            height :

            gravity :
                 (Default value = Q_(9.8)
            "m/s^2") :


            Returns
            -------

            """
            return sqrt(2 * height / gravity)

        lunar_module_height = Q_(10, "m")
        t1 = calculate_time_to_fall(lunar_module_height)
        # print(t1)
        self.assertAlmostEqual(t1, Q_(1.4285714285714286, "s"))

        moon_gravity = Q_(1.625, "m/s^2")
        t2 = calculate_time_to_fall(lunar_module_height, moon_gravity)
        self.assertAlmostEqual(t2, Q_(3.508232077228117, "s"))

    def test_issue625b(self):
        Q_ = ureg.Quantity

        @ureg.wraps("=A*B", ("=A", "=B"))
        def get_displacement(time, rate=Q_(1, "m/s")):
            """Calculates displacement from a duration and default rate.

            Parameters
            ----------
            time :

            rate :
                 (Default value = Q_(1)
            "m/s") :


            Returns
            -------

            """
            return time * rate

        d1 = get_displacement(Q_(2, "s"))
        self.assertAlmostEqual(d1, Q_(2, "m"))

        d2 = get_displacement(Q_(2, "s"), Q_(1, "deg/s"))
        self.assertAlmostEqual(d2, Q_(2, " deg"))

    def test_issue625c(self):
        u = UnitRegistry()

        @u.wraps("=A*B*C", ("=A", "=B", "=C"))
        def get_product(a=2 * u.m, b=3 * u.m, c=5 * u.m):
            return a * b * c

        self.assertEqual(get_product(a=3 * u.m), 45 * u.m ** 3)
        self.assertEqual(get_product(b=2 * u.m), 20 * u.m ** 3)
        self.assertEqual(get_product(c=1 * u.dimensionless), 6 * u.m ** 2)

    def test_issue655a(self):
        distance = 1 * ureg.m
        time = 1 * ureg.s
        velocity = distance / time
        self.assertEqual(distance.check("[length]"), True)
        self.assertEqual(distance.check("[time]"), False)
        self.assertEqual(velocity.check("[length] / [time]"), True)
        self.assertEqual(velocity.check("1 / [time] * [length]"), True)

    def test_issue655b(self):
        Q_ = ureg.Quantity

        @ureg.check("[length]", "[length]/[time]^2")
        def pendulum_period(length, G=Q_(1, "standard_gravity")):
            # print(length)
            return (2 * math.pi * (length / G) ** 0.5).to("s")

        length = Q_(1, ureg.m)
        # Assume earth gravity
        t = pendulum_period(length)
        self.assertAlmostEqual(t, Q_("2.0064092925890407 second"))
        # Use moon gravity
        moon_gravity = Q_(1.625, "m/s^2")
        t = pendulum_period(length, moon_gravity)
        self.assertAlmostEqual(t, Q_("4.928936075204336 second"))

    def test_issue783(self):
        assert not ureg("g") == []

    def test_issue856(self):
        ph1 = ParserHelper(scale=123)
        ph2 = copy.deepcopy(ph1)
        assert ph2.scale == ph1.scale

        ureg1 = UnitRegistry()
        ureg2 = copy.deepcopy(ureg1)
        # Very basic functionality test
        assert ureg2("1 t").to("kg").magnitude == 1000

    def test_issue856b(self):
        # Test that, after a deepcopy(), the two UnitRegistries are
        # independent from each other
        ureg1 = UnitRegistry()
        ureg2 = copy.deepcopy(ureg1)
        ureg1.define("test123 = 123 kg")
        ureg2.define("test123 = 456 kg")
        assert ureg1("1 test123").to("kg").magnitude == 123
        assert ureg2("1 test123").to("kg").magnitude == 456

    def test_issue876(self):
        # Same hash must not imply equality.

        # As an implementation detail of CPython, hash(-1) == hash(-2).
        # This test is useless in potential alternative Python implementations where
        # hash(-1) != hash(-2); one would need to find hash collisions specific for each
        # implementation

        a = UnitsContainer({"[mass]": -1})
        b = UnitsContainer({"[mass]": -2})
        c = UnitsContainer({"[mass]": -3})

        # Guarantee working on alternative Python implementations
        assert (hash(-1) == hash(-2)) == (hash(a) == hash(b))
        assert (hash(-1) == hash(-3)) == (hash(a) == hash(c))
        assert a != b
        assert a != c

    def test_issue902(self):
        ureg = UnitRegistry(auto_reduce_dimensions=True)
        velocity = 1 * ureg.m / ureg.s
        cross_section = 1 * ureg.um ** 2
        result = cross_section / velocity
        assert result == 1e-12 * ureg.m * ureg.s

    def test_issue912(self):
        """pprint.pformat() invokes sorted() on large sets and frozensets and graciously
        handles TypeError, but not generic Exceptions. This test will fail if
        pint.DimensionalityError stops being a subclass of TypeError.

        Parameters
        ----------

        Returns
        -------

        """
        meter_units = ureg.get_compatible_units(ureg.meter)
        hertz_units = ureg.get_compatible_units(ureg.hertz)
        pprint.pformat(meter_units | hertz_units)

    def test_issue932(self):
        q = ureg.Quantity("1 kg")
        with self.assertRaises(DimensionalityError):
            q.to("joule")
        ureg.enable_contexts("energy", *(Context() for _ in range(20)))
        q.to("joule")
        ureg.disable_contexts()
        with self.assertRaises(DimensionalityError):
            q.to("joule")

    def test_issue960(self):
        q = (1 * ureg.nanometer).to_compact("micrometer")
        assert q.units == ureg.nanometer
        assert q.magnitude == 1

    def test_issue1032(self):
        class MultiplicativeDictionary(dict):
            def __rmul__(self, other):
                return self.__class__(
                    {key: value * other for key, value in self.items()}
                )

        q = 3 * ureg.s
        d = MultiplicativeDictionary({4: 5, 6: 7})
        assert q * d == MultiplicativeDictionary({4: 15 * ureg.s, 6: 21 * ureg.s})
        with self.assertRaises(TypeError):
            d * q

    @helpers.requires_numpy()
    def test_issue973(self):
        """Verify that an empty array Quantity can be created through multiplication."""
        q0 = np.array([]) * ureg.m  # by Unit
        q1 = np.array([]) * ureg("m")  # by Quantity
        assert isinstance(q0, ureg.Quantity)
        assert isinstance(q1, ureg.Quantity)
        assert len(q0) == len(q1) == 0

    def test_issue1058(self):
        """ verify that auto-reducing quantities with three or more units
        of same base type succeeds """
        q = 1 * ureg.mg / ureg.g / ureg.kg
        q.ito_reduced_units()
        self.assertIsInstance(q, ureg.Quantity)

    def test_issue1062_issue1097(self):
        # Must not be used by any other tests
        assert "nanometer" not in ureg._units
        for i in range(5):
            ctx = Context.from_lines(["@context _", "cal = 4 J"])
            with ureg.context("sp", ctx):
                q = ureg.Quantity(1, "nm")
                q.to("J")

    def test_issue1086(self):
        # units with prefixes should correctly test as 'in' the registry
        assert "bits" in ureg
        assert "gigabits" in ureg
        assert "meters" in ureg
        assert "kilometers" in ureg
        # unknown or incorrect units should test as 'not in' the registry
        assert "magicbits" not in ureg
        assert "unknownmeters" not in ureg
        assert "gigatrees" not in ureg

    def test_issue1112(self):
        ureg = UnitRegistry(
            """
            m = [length]
            g = [mass]
            s = [time]

            ft = 0.305 m
            lb = 454 g

            @context c1
                [time]->[length] : value * 10 m/s
            @end
            @context c2
                ft = 0.3 m
            @end
            @context c3
                lb = 500 g
            @end
            """.splitlines()
        )
        ureg.enable_contexts("c1")
        ureg.enable_contexts("c2")
        ureg.enable_contexts("c3")

    @helpers.requires_numpy()
    def test_issue1144_1102(self):
        # Performing operations shouldn't modify the original objects
        # Issue 1144
        ddc = "delta_degree_Celsius"
        q1 = ureg.Quantity([-287.78, -32.24, -1.94], ddc)
        q2 = ureg.Quantity(70.0, "degree_Fahrenheit")
        q1 - q2
        assert all(q1 == ureg.Quantity([-287.78, -32.24, -1.94], ddc))
        assert q2 == ureg.Quantity(70.0, "degree_Fahrenheit")
        q2 - q1
        assert all(q1 == ureg.Quantity([-287.78, -32.24, -1.94], ddc))
        assert q2 == ureg.Quantity(70.0, "degree_Fahrenheit")
        # Issue 1102
        val = [30.0, 45.0, 60.0] * ureg.degree
        val == 1
        1 == val
        assert all(val == ureg.Quantity([30.0, 45.0, 60.0], "degree"))
        # Test for another bug identified by searching on "_convert_magnitude"
        q2 = ureg.Quantity(3, "degree_Kelvin")
        q1 - q2
        assert all(q1 == ureg.Quantity([-287.78, -32.24, -1.94], ddc))

    @helpers.requires_numpy()
    def test_issue_1136(self):
        assert (2 ** ureg.Quantity([2, 3], "") == 2 ** np.array([2, 3])).all()

        with pytest.raises(DimensionalityError):
            2 ** ureg.Quantity([2, 3], "m")

    def test_issue1175(self):
        import pickle

        foo1 = get_application_registry().Quantity(1, "s")
        foo2 = pickle.loads(pickle.dumps(foo1))
        self.assertIsInstance(foo1, foo2.__class__)
        self.assertIsInstance(foo2, foo1.__class__)


if np is not None:

    @pytest.mark.parametrize(
        "callable",
        [
            lambda x: np.sin(x / x.units),  # Issue 399
            lambda x: np.cos(x / x.units),  # Issue 399
            np.isfinite,  # Issue 481
            np.shape,  # Issue 509
            np.size,  # Issue 509
            np.sqrt,  # Issue 622
            lambda x: x.mean(),  # Issue 678
            lambda x: x.copy(),  # Issue 678
            np.array,
            lambda x: x.conjugate,
        ],
    )
    @pytest.mark.parametrize(
        "q",
        [
            pytest.param(ureg.Quantity(1, "m"), id="python scalar int"),
            pytest.param(ureg.Quantity([1, 2, 3, 4], "m"), id="array int"),
            pytest.param(ureg.Quantity([1], "m")[0], id="numpy scalar int"),
            pytest.param(ureg.Quantity(1.0, "m"), id="python scalar float"),
            pytest.param(ureg.Quantity([1.0, 2.0, 3.0, 4.0], "m"), id="array float"),
            pytest.param(ureg.Quantity([1.0], "m")[0], id="numpy scalar float"),
        ],
    )
    def test_issue925(callable, q):
        # Test for immutability of type
        type_before = type(q._magnitude)
        callable(q)
        assert isinstance(q._magnitude, type_before)
