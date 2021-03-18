import copy
import math
import operator as op
import pickle
from decimal import Decimal
from fractions import Fraction

from pint import DimensionalityError, OffsetUnitCalculusError, UnitRegistry
from pint.testsuite import QuantityTestCase
from pint.testsuite.parameterized import ParameterizedTestMixin as ParameterizedTestCase
from pint.unit import UnitsContainer


class FakeWrapper:
    # Used in test_upcast_type_rejection_on_creation
    def __init__(self, q):
        self.q = q


class NonIntTypeQuantityTestCase(QuantityTestCase):

    NON_INT_TYPE = None

    @classmethod
    def setUpClass(cls):
        cls.ureg = UnitRegistry(
            force_ndarray=cls.FORCE_NDARRAY, non_int_type=cls.NON_INT_TYPE
        )
        cls.Q_ = cls.ureg.Quantity
        cls.U_ = cls.ureg.Unit

    def assertQuantityAlmostEqual(
        self, first, second, rtol="1e-07", atol="0", msg=None
    ):

        if isinstance(first, self.Q_):
            self.assertIsInstance(first.m, (self.NON_INT_TYPE, int))
        else:
            self.assertIsInstance(first, (self.NON_INT_TYPE, int))

        if isinstance(second, self.Q_):
            self.assertIsInstance(second.m, (self.NON_INT_TYPE, int))
        else:
            self.assertIsInstance(second, (self.NON_INT_TYPE, int))
        super().assertQuantityAlmostEqual(
            first, second, self.NON_INT_TYPE(rtol), self.NON_INT_TYPE(atol), msg
        )

    def QP_(self, value, units):
        self.assertIsInstance(value, str)
        return self.Q_(self.NON_INT_TYPE(value), units)


class _TestBasic:
    def test_quantity_creation(self):

        value = self.NON_INT_TYPE("4.2")

        for args in (
            (value, "meter"),
            (value, UnitsContainer(meter=1)),
            (value, self.ureg.meter),
            ("4.2*meter",),
            ("4.2/meter**(-1)",),
            (self.Q_(value, "meter"),),
        ):
            x = self.Q_(*args)
            self.assertEqual(x.magnitude, value)
            self.assertEqual(x.units, self.ureg.UnitsContainer(meter=1))

        x = self.Q_(value, UnitsContainer(length=1))
        y = self.Q_(x)
        self.assertEqual(x.magnitude, y.magnitude)
        self.assertEqual(x.units, y.units)
        self.assertIsNot(x, y)

        x = self.Q_(value, None)
        self.assertEqual(x.magnitude, value)
        self.assertEqual(x.units, UnitsContainer())

        with self.capture_log() as buffer:
            self.assertEqual(
                value * self.ureg.meter,
                self.Q_(value, self.NON_INT_TYPE("2") * self.ureg.meter),
            )
            self.assertEqual(len(buffer), 1)

    def test_quantity_comparison(self):
        x = self.QP_("4.2", "meter")
        y = self.QP_("4.2", "meter")
        z = self.QP_("5", "meter")
        j = self.QP_("5", "meter*meter")

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
        self.assertEqual(self.QP_("0", "meter"), self.QP_("0", "centimeter"))
        self.assertNotEqual(self.QP_("0", "meter"), self.QP_("0", "second"))

        self.assertLess(self.QP_("10", "meter"), self.QP_("5", "kilometer"))

    def test_quantity_comparison_convert(self):
        self.assertEqual(self.QP_("1000", "millimeter"), self.QP_("1", "meter"))
        self.assertEqual(
            self.QP_("1000", "millimeter/min"),
            self.Q_(
                self.NON_INT_TYPE("1000") / self.NON_INT_TYPE("60"), "millimeter/s"
            ),
        )

    def test_quantity_hash(self):
        x = self.QP_("4.2", "meter")
        x2 = self.QP_("4200", "millimeter")
        y = self.QP_("2", "second")
        z = self.QP_("0.5", "hertz")
        self.assertEqual(hash(x), hash(x2))

        # Dimensionless equality
        self.assertEqual(hash(y * z), hash(1.0))

        # Dimensionless equality from a different unit registry
        ureg2 = UnitRegistry(force_ndarray=self.FORCE_NDARRAY)
        y2 = ureg2.Quantity(self.NON_INT_TYPE("2"), "second")
        z2 = ureg2.Quantity(self.NON_INT_TYPE("0.5"), "hertz")
        self.assertEqual(hash(y * z), hash(y2 * z2))

    def test_to_base_units(self):
        x = self.Q_("1*inch")
        self.assertQuantityAlmostEqual(x.to_base_units(), self.QP_("0.0254", "meter"))
        x = self.Q_("1*inch*inch")
        self.assertQuantityAlmostEqual(
            x.to_base_units(),
            self.Q_(
                self.NON_INT_TYPE("0.0254") ** self.NON_INT_TYPE("2.0"), "meter*meter"
            ),
        )
        x = self.Q_("1*inch/minute")
        self.assertQuantityAlmostEqual(
            x.to_base_units(),
            self.Q_(
                self.NON_INT_TYPE("0.0254") / self.NON_INT_TYPE("60"), "meter/second"
            ),
        )

    def test_convert(self):
        self.assertQuantityAlmostEqual(
            self.Q_("2 inch").to("meter"),
            self.Q_(self.NON_INT_TYPE("2") * self.NON_INT_TYPE("0.0254"), "meter"),
        )
        self.assertQuantityAlmostEqual(
            self.Q_("2 meter").to("inch"),
            self.Q_(self.NON_INT_TYPE("2") / self.NON_INT_TYPE("0.0254"), "inch"),
        )
        self.assertQuantityAlmostEqual(
            self.Q_("2 sidereal_year").to("second"), self.QP_("63116297.5325", "second")
        )
        self.assertQuantityAlmostEqual(
            self.Q_("2.54 centimeter/second").to("inch/second"),
            self.Q_("1 inch/second"),
        )
        self.assertAlmostEqual(self.Q_("2.54 centimeter").to("inch").magnitude, 1)
        self.assertAlmostEqual(self.Q_("2 second").to("millisecond").magnitude, 2000)

    def test_convert_from(self):
        x = self.Q_("2*inch")
        meter = self.ureg.meter

        # from quantity
        self.assertQuantityAlmostEqual(
            meter.from_(x),
            self.Q_(self.NON_INT_TYPE("2") * self.NON_INT_TYPE("0.0254"), "meter"),
        )
        self.assertQuantityAlmostEqual(
            meter.m_from(x), self.NON_INT_TYPE("2") * self.NON_INT_TYPE("0.0254")
        )

        # from unit
        self.assertQuantityAlmostEqual(
            meter.from_(self.ureg.inch), self.QP_("0.0254", "meter")
        )
        self.assertQuantityAlmostEqual(
            meter.m_from(self.ureg.inch), self.NON_INT_TYPE("0.0254")
        )

        # from number
        self.assertQuantityAlmostEqual(
            meter.from_(2, strict=False), self.QP_("2", "meter")
        )
        self.assertQuantityAlmostEqual(
            meter.m_from(self.NON_INT_TYPE("2"), strict=False), self.NON_INT_TYPE("2")
        )

        # from number (strict mode)
        self.assertRaises(ValueError, meter.from_, self.NON_INT_TYPE("2"))
        self.assertRaises(ValueError, meter.m_from, self.NON_INT_TYPE("2"))

    def test_context_attr(self):
        self.assertEqual(self.ureg.meter, self.QP_("1", "meter"))

    def test_both_symbol(self):
        self.assertEqual(self.QP_("2", "ms"), self.QP_("2", "millisecond"))
        self.assertEqual(self.QP_("2", "cm"), self.QP_("2", "centimeter"))

    def test_dimensionless_units(self):
        twopi = self.NON_INT_TYPE("2") * self.ureg.pi
        self.assertAlmostEqual(self.QP_("360", "degree").to("radian").magnitude, twopi)
        self.assertAlmostEqual(self.Q_(twopi, "radian"), self.QP_("360", "degree"))
        self.assertEqual(self.QP_("1", "radian").dimensionality, UnitsContainer())
        self.assertTrue(self.QP_("1", "radian").dimensionless)
        self.assertFalse(self.QP_("1", "radian").unitless)

        self.assertEqual(self.QP_("1", "meter") / self.QP_("1", "meter"), 1)
        self.assertEqual((self.QP_("1", "meter") / self.QP_("1", "mm")).to(""), 1000)

        self.assertEqual(self.Q_(10) // self.QP_("360", "degree"), 1)
        self.assertEqual(self.QP_("400", "degree") // self.Q_(twopi), 1)
        self.assertEqual(self.QP_("400", "degree") // twopi, 1)
        self.assertEqual(7 // self.QP_("360", "degree"), 1)

    def test_offset(self):
        self.assertQuantityAlmostEqual(
            self.QP_("0", "kelvin").to("kelvin"), self.QP_("0", "kelvin")
        )
        self.assertQuantityAlmostEqual(
            self.QP_("0", "degC").to("kelvin"), self.QP_("273.15", "kelvin")
        )
        self.assertQuantityAlmostEqual(
            self.QP_("0", "degF").to("kelvin"),
            self.QP_("255.372222", "kelvin"),
            rtol=0.01,
        )

        self.assertQuantityAlmostEqual(
            self.QP_("100", "kelvin").to("kelvin"), self.QP_("100", "kelvin")
        )
        self.assertQuantityAlmostEqual(
            self.QP_("100", "degC").to("kelvin"), self.QP_("373.15", "kelvin")
        )
        self.assertQuantityAlmostEqual(
            self.QP_("100", "degF").to("kelvin"),
            self.QP_("310.92777777", "kelvin"),
            rtol=0.01,
        )

        self.assertQuantityAlmostEqual(
            self.QP_("0", "kelvin").to("degC"), self.QP_("-273.15", "degC")
        )
        self.assertQuantityAlmostEqual(
            self.QP_("100", "kelvin").to("degC"), self.QP_("-173.15", "degC")
        )
        self.assertQuantityAlmostEqual(
            self.QP_("0", "kelvin").to("degF"), self.QP_("-459.67", "degF"), rtol=0.01
        )
        self.assertQuantityAlmostEqual(
            self.QP_("100", "kelvin").to("degF"), self.QP_("-279.67", "degF"), rtol=0.01
        )

        self.assertQuantityAlmostEqual(
            self.QP_("32", "degF").to("degC"), self.QP_("0", "degC"), atol=0.01
        )
        self.assertQuantityAlmostEqual(
            self.QP_("100", "degC").to("degF"), self.QP_("212", "degF"), atol=0.01
        )

        self.assertQuantityAlmostEqual(
            self.QP_("54", "degF").to("degC"), self.QP_("12.2222", "degC"), atol=0.01
        )
        self.assertQuantityAlmostEqual(
            self.QP_("12", "degC").to("degF"), self.QP_("53.6", "degF"), atol=0.01
        )

        self.assertQuantityAlmostEqual(
            self.QP_("12", "kelvin").to("degC"), self.QP_("-261.15", "degC"), atol=0.01
        )
        self.assertQuantityAlmostEqual(
            self.QP_("12", "degC").to("kelvin"), self.QP_("285.15", "kelvin"), atol=0.01
        )

        self.assertQuantityAlmostEqual(
            self.QP_("12", "kelvin").to("degR"), self.QP_("21.6", "degR"), atol=0.01
        )
        self.assertQuantityAlmostEqual(
            self.QP_("12", "degR").to("kelvin"),
            self.QP_("6.66666667", "kelvin"),
            atol=0.01,
        )

        self.assertQuantityAlmostEqual(
            self.QP_("12", "degC").to("degR"), self.QP_("513.27", "degR"), atol=0.01
        )
        self.assertQuantityAlmostEqual(
            self.QP_("12", "degR").to("degC"),
            self.QP_("-266.483333", "degC"),
            atol=0.01,
        )

    def test_offset_delta(self):
        self.assertQuantityAlmostEqual(
            self.QP_("0", "delta_degC").to("kelvin"), self.QP_("0", "kelvin")
        )
        self.assertQuantityAlmostEqual(
            self.QP_("0", "delta_degF").to("kelvin"), self.QP_("0", "kelvin"), rtol=0.01
        )

        self.assertQuantityAlmostEqual(
            self.QP_("100", "kelvin").to("delta_degC"), self.QP_("100", "delta_degC")
        )
        self.assertQuantityAlmostEqual(
            self.QP_("100", "kelvin").to("delta_degF"),
            self.QP_("180", "delta_degF"),
            rtol=0.01,
        )
        self.assertQuantityAlmostEqual(
            self.QP_("100", "delta_degF").to("kelvin"),
            self.QP_("55.55555556", "kelvin"),
            rtol=0.01,
        )
        self.assertQuantityAlmostEqual(
            self.QP_("100", "delta_degC").to("delta_degF"),
            self.QP_("180", "delta_degF"),
            rtol=0.01,
        )
        self.assertQuantityAlmostEqual(
            self.QP_("100", "delta_degF").to("delta_degC"),
            self.QP_("55.55555556", "delta_degC"),
            rtol=0.01,
        )

        self.assertQuantityAlmostEqual(
            self.QP_("12.3", "delta_degC").to("delta_degF"),
            self.QP_("22.14", "delta_degF"),
            rtol=0.01,
        )

    def test_pickle(self):
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            for magnitude, unit in (
                ("32", ""),
                ("2.4", ""),
                ("32", "m/s"),
                ("2.4", "m/s"),
            ):
                with self.subTest(protocol=protocol, magnitude=magnitude, unit=unit):
                    q1 = self.QP_(magnitude, unit)
                    q2 = pickle.loads(pickle.dumps(q1, protocol))
                    self.assertEqual(q1, q2)

    def test_notiter(self):
        # Verify that iter() crashes immediately, without needing to draw any
        # element from it, if the magnitude isn't iterable
        x = self.QP_("1", "m")
        with self.assertRaises(TypeError):
            iter(x)


class _TestQuantityBasicMath:

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
        func(
            op.add, x, y, self.Q_(unit + self.NON_INT_TYPE("2.54") * unit, "centimeter")
        )
        func(
            op.add,
            y,
            x,
            self.Q_(unit + unit / (self.NON_INT_TYPE("2.54") * unit), "inch"),
        )
        func(op.add, a, unit, self.Q_(unit + unit, None))
        self.assertRaises(DimensionalityError, op.add, self.NON_INT_TYPE("10"), x)
        self.assertRaises(DimensionalityError, op.add, x, self.NON_INT_TYPE("10"))
        self.assertRaises(DimensionalityError, op.add, x, z)

        func(op.sub, x, x, self.Q_(unit - unit, "centimeter"))
        func(
            op.sub, x, y, self.Q_(unit - self.NON_INT_TYPE("2.54") * unit, "centimeter")
        )
        func(
            op.sub,
            y,
            x,
            self.Q_(unit - unit / (self.NON_INT_TYPE("2.54") * unit), "inch"),
        )
        func(op.sub, a, unit, self.Q_(unit - unit, None))
        self.assertRaises(DimensionalityError, op.sub, self.NON_INT_TYPE("10"), x)
        self.assertRaises(DimensionalityError, op.sub, x, self.NON_INT_TYPE("10"))
        self.assertRaises(DimensionalityError, op.sub, x, z)

    def _test_quantity_iadd_isub(self, unit, func):
        x = self.Q_(unit, "centimeter")
        y = self.Q_(unit, "inch")
        z = self.Q_(unit, "second")
        a = self.Q_(unit, None)

        func(op.iadd, x, x, self.Q_(unit + unit, "centimeter"))
        func(
            op.iadd,
            x,
            y,
            self.Q_(unit + self.NON_INT_TYPE("2.54") * unit, "centimeter"),
        )
        func(op.iadd, y, x, self.Q_(unit + unit / self.NON_INT_TYPE("2.54"), "inch"))
        func(op.iadd, a, unit, self.Q_(unit + unit, None))
        self.assertRaises(DimensionalityError, op.iadd, self.NON_INT_TYPE("10"), x)
        self.assertRaises(DimensionalityError, op.iadd, x, self.NON_INT_TYPE("10"))
        self.assertRaises(DimensionalityError, op.iadd, x, z)

        func(op.isub, x, x, self.Q_(unit - unit, "centimeter"))
        func(op.isub, x, y, self.Q_(unit - self.NON_INT_TYPE("2.54"), "centimeter"))
        func(op.isub, y, x, self.Q_(unit - unit / self.NON_INT_TYPE("2.54"), "inch"))
        func(op.isub, a, unit, self.Q_(unit - unit, None))
        self.assertRaises(DimensionalityError, op.sub, self.NON_INT_TYPE("10"), x)
        self.assertRaises(DimensionalityError, op.sub, x, self.NON_INT_TYPE("10"))
        self.assertRaises(DimensionalityError, op.sub, x, z)

    def _test_quantity_mul_div(self, unit, func):
        func(op.mul, unit * self.NON_INT_TYPE("10"), "4.2*meter", "42*meter", unit)
        func(op.mul, "4.2*meter", unit * self.NON_INT_TYPE("10"), "42*meter", unit)
        func(op.mul, "4.2*meter", "10*inch", "42*meter*inch", unit)
        func(op.truediv, unit * self.NON_INT_TYPE("42"), "4.2*meter", "10/meter", unit)
        func(
            op.truediv, "4.2*meter", unit * self.NON_INT_TYPE("10"), "0.42*meter", unit
        )
        func(op.truediv, "4.2*meter", "10*inch", "0.42*meter/inch", unit)

    def _test_quantity_imul_idiv(self, unit, func):
        # func(op.imul, 10.0, '4.2*meter', '42*meter')
        func(op.imul, "4.2*meter", self.NON_INT_TYPE("10"), "42*meter", unit)
        func(op.imul, "4.2*meter", "10*inch", "42*meter*inch", unit)
        # func(op.truediv, 42, '4.2*meter', '10/meter')
        func(
            op.itruediv, "4.2*meter", unit * self.NON_INT_TYPE("10"), "0.42*meter", unit
        )
        func(op.itruediv, "4.2*meter", "10*inch", "0.42*meter/inch", unit)

    def _test_quantity_floordiv(self, unit, func):
        a = self.Q_("10*meter")
        b = self.Q_("3*second")
        self.assertRaises(DimensionalityError, op.floordiv, a, b)
        self.assertRaises(DimensionalityError, op.floordiv, self.NON_INT_TYPE("3"), b)
        self.assertRaises(DimensionalityError, op.floordiv, a, self.NON_INT_TYPE("3"))
        self.assertRaises(DimensionalityError, op.ifloordiv, a, b)
        self.assertRaises(DimensionalityError, op.ifloordiv, self.NON_INT_TYPE("3"), b)
        self.assertRaises(DimensionalityError, op.ifloordiv, a, self.NON_INT_TYPE("3"))
        func(
            op.floordiv,
            unit * self.NON_INT_TYPE("10"),
            "4.2*meter/meter",
            self.NON_INT_TYPE("2"),
            unit,
        )
        func(op.floordiv, "10*meter", "4.2*inch", self.NON_INT_TYPE("93"), unit)

    def _test_quantity_mod(self, unit, func):
        a = self.Q_("10*meter")
        b = self.Q_("3*second")
        self.assertRaises(DimensionalityError, op.mod, a, b)
        self.assertRaises(DimensionalityError, op.mod, 3, b)
        self.assertRaises(DimensionalityError, op.mod, a, 3)
        self.assertRaises(DimensionalityError, op.imod, a, b)
        self.assertRaises(DimensionalityError, op.imod, 3, b)
        self.assertRaises(DimensionalityError, op.imod, a, 3)
        func(
            op.mod,
            unit * self.NON_INT_TYPE("10"),
            "4.2*meter/meter",
            self.NON_INT_TYPE("1.6"),
            unit,
        )

    def _test_quantity_ifloordiv(self, unit, func):
        func(
            op.ifloordiv,
            self.NON_INT_TYPE("10"),
            "4.2*meter/meter",
            self.NON_INT_TYPE("2"),
            unit,
        )
        func(op.ifloordiv, "10*meter", "4.2*inch", self.NON_INT_TYPE("93"), unit)

    def _test_quantity_divmod_one(self, a, b):
        if isinstance(a, str):
            a = self.Q_(a)
        if isinstance(b, str):
            b = self.Q_(b)

        q, r = divmod(a, b)
        self.assertEqual(q, a // b)
        self.assertEqual(r, a % b)
        self.assertQuantityEqual(a, (q * b) + r)
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

        # Disabling these tests as it yields different results without Quantities
        # >>> from decimal import Decimal as D
        # >>> divmod(-D('100'), D('3'))
        # (Decimal('-33'), Decimal('-1'))
        # >>> divmod(-100, 3)
        # (-34, 2)

        # self._test_quantity_divmod_one("-10*meter", "4.2*inch")
        # self._test_quantity_divmod_one("-10*meter", "-4.2*inch")
        # self._test_quantity_divmod_one("10*meter", "-4.2*inch")

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

    def test_quantity_abs_round(self):

        value = self.NON_INT_TYPE("4.2")
        x = self.Q_(-value, "meter")
        y = self.Q_(value, "meter")

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
        x = self.QP_("-4.2", None)
        y = self.QP_("4.2", None)
        z = self.QP_("1", "meter")
        for fun in (float, complex):
            self.assertEqual(fun(x), fun(x.magnitude))
            self.assertEqual(fun(y), fun(y.magnitude))
            self.assertRaises(DimensionalityError, fun, z)

    def test_not_inplace(self):
        self._test_numeric(self.NON_INT_TYPE("1.0"), self._test_not_inplace)


class _TestOffsetUnitMath(ParameterizedTestCase):
    def setup(self):
        self.ureg.autoconvert_offset_to_baseunit = False
        self.ureg.default_as_delta = True

    additions = [
        # --- input tuple -------------------- | -- expected result --
        ((("100", "kelvin"), ("10", "kelvin")), ("110", "kelvin")),
        ((("100", "kelvin"), ("10", "degC")), "error"),
        ((("100", "kelvin"), ("10", "degF")), "error"),
        ((("100", "kelvin"), ("10", "degR")), ("105.56", "kelvin")),
        ((("100", "kelvin"), ("10", "delta_degC")), ("110", "kelvin")),
        ((("100", "kelvin"), ("10", "delta_degF")), ("105.56", "kelvin")),
        ((("100", "degC"), ("10", "kelvin")), "error"),
        ((("100", "degC"), ("10", "degC")), "error"),
        ((("100", "degC"), ("10", "degF")), "error"),
        ((("100", "degC"), ("10", "degR")), "error"),
        ((("100", "degC"), ("10", "delta_degC")), ("110", "degC")),
        ((("100", "degC"), ("10", "delta_degF")), ("105.56", "degC")),
        ((("100", "degF"), ("10", "kelvin")), "error"),
        ((("100", "degF"), ("10", "degC")), "error"),
        ((("100", "degF"), ("10", "degF")), "error"),
        ((("100", "degF"), ("10", "degR")), "error"),
        ((("100", "degF"), ("10", "delta_degC")), ("118", "degF")),
        ((("100", "degF"), ("10", "delta_degF")), ("110", "degF")),
        ((("100", "degR"), ("10", "kelvin")), ("118", "degR")),
        ((("100", "degR"), ("10", "degC")), "error"),
        ((("100", "degR"), ("10", "degF")), "error"),
        ((("100", "degR"), ("10", "degR")), ("110", "degR")),
        ((("100", "degR"), ("10", "delta_degC")), ("118", "degR")),
        ((("100", "degR"), ("10", "delta_degF")), ("110", "degR")),
        ((("100", "delta_degC"), ("10", "kelvin")), ("110", "kelvin")),
        ((("100", "delta_degC"), ("10", "degC")), ("110", "degC")),
        ((("100", "delta_degC"), ("10", "degF")), ("190", "degF")),
        ((("100", "delta_degC"), ("10", "degR")), ("190", "degR")),
        ((("100", "delta_degC"), ("10", "delta_degC")), ("110", "delta_degC")),
        ((("100", "delta_degC"), ("10", "delta_degF")), ("105.56", "delta_degC")),
        ((("100", "delta_degF"), ("10", "kelvin")), ("65.56", "kelvin")),
        ((("100", "delta_degF"), ("10", "degC")), ("65.56", "degC")),
        ((("100", "delta_degF"), ("10", "degF")), ("110", "degF")),
        ((("100", "delta_degF"), ("10", "degR")), ("110", "degR")),
        ((("100", "delta_degF"), ("10", "delta_degC")), ("118", "delta_degF")),
        ((("100", "delta_degF"), ("10", "delta_degF")), ("110", "delta_degF")),
    ]

    @ParameterizedTestCase.parameterize(("input", "expected_output"), additions)
    def test_addition(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = False
        qin1, qin2 = input_tuple
        q1, q2 = self.QP_(*qin1), self.QP_(*qin2)
        # update input tuple with new values to have correct values on failure
        input_tuple = q1, q2
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.add, q1, q2)
        else:
            expected = self.QP_(*expected)
            self.assertEqual(op.add(q1, q2).units, expected.units)
            self.assertQuantityAlmostEqual(op.add(q1, q2), expected, atol="0.01")

    subtractions = [
        ((("100", "kelvin"), ("10", "kelvin")), ("90", "kelvin")),
        ((("100", "kelvin"), ("10", "degC")), ("-183.15", "kelvin")),
        ((("100", "kelvin"), ("10", "degF")), ("-160.93", "kelvin")),
        ((("100", "kelvin"), ("10", "degR")), ("94.44", "kelvin")),
        ((("100", "kelvin"), ("10", "delta_degC")), ("90", "kelvin")),
        ((("100", "kelvin"), ("10", "delta_degF")), ("94.44", "kelvin")),
        ((("100", "degC"), ("10", "kelvin")), ("363.15", "delta_degC")),
        ((("100", "degC"), ("10", "degC")), ("90", "delta_degC")),
        ((("100", "degC"), ("10", "degF")), ("112.22", "delta_degC")),
        ((("100", "degC"), ("10", "degR")), ("367.59", "delta_degC")),
        ((("100", "degC"), ("10", "delta_degC")), ("90", "degC")),
        ((("100", "degC"), ("10", "delta_degF")), ("94.44", "degC")),
        ((("100", "degF"), ("10", "kelvin")), ("541.67", "delta_degF")),
        ((("100", "degF"), ("10", "degC")), ("50", "delta_degF")),
        ((("100", "degF"), ("10", "degF")), ("90", "delta_degF")),
        ((("100", "degF"), ("10", "degR")), ("549.67", "delta_degF")),
        ((("100", "degF"), ("10", "delta_degC")), ("82", "degF")),
        ((("100", "degF"), ("10", "delta_degF")), ("90", "degF")),
        ((("100", "degR"), ("10", "kelvin")), ("82", "degR")),
        ((("100", "degR"), ("10", "degC")), ("-409.67", "degR")),
        ((("100", "degR"), ("10", "degF")), ("-369.67", "degR")),
        ((("100", "degR"), ("10", "degR")), ("90", "degR")),
        ((("100", "degR"), ("10", "delta_degC")), ("82", "degR")),
        ((("100", "degR"), ("10", "delta_degF")), ("90", "degR")),
        ((("100", "delta_degC"), ("10", "kelvin")), ("90", "kelvin")),
        ((("100", "delta_degC"), ("10", "degC")), ("90", "degC")),
        ((("100", "delta_degC"), ("10", "degF")), ("170", "degF")),
        ((("100", "delta_degC"), ("10", "degR")), ("170", "degR")),
        ((("100", "delta_degC"), ("10", "delta_degC")), ("90", "delta_degC")),
        ((("100", "delta_degC"), ("10", "delta_degF")), ("94.44", "delta_degC")),
        ((("100", "delta_degF"), ("10", "kelvin")), ("45.56", "kelvin")),
        ((("100", "delta_degF"), ("10", "degC")), ("45.56", "degC")),
        ((("100", "delta_degF"), ("10", "degF")), ("90", "degF")),
        ((("100", "delta_degF"), ("10", "degR")), ("90", "degR")),
        ((("100", "delta_degF"), ("10", "delta_degC")), ("82", "delta_degF")),
        ((("100", "delta_degF"), ("10", "delta_degF")), ("90", "delta_degF")),
    ]

    @ParameterizedTestCase.parameterize(("input", "expected_output"), subtractions)
    def test_subtraction(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = False
        qin1, qin2 = input_tuple
        q1, q2 = self.QP_(*qin1), self.QP_(*qin2)
        input_tuple = q1, q2
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.sub, q1, q2)
        else:
            expected = self.QP_(*expected)
            self.assertEqual(op.sub(q1, q2).units, expected.units)
            self.assertQuantityAlmostEqual(op.sub(q1, q2), expected, atol=0.01)

    multiplications = [
        ((("100", "kelvin"), ("10", "kelvin")), ("1000", "kelvin**2")),
        ((("100", "kelvin"), ("10", "degC")), "error"),
        ((("100", "kelvin"), ("10", "degF")), "error"),
        ((("100", "kelvin"), ("10", "degR")), ("1000", "kelvin*degR")),
        ((("100", "kelvin"), ("10", "delta_degC")), ("1000", "kelvin*delta_degC")),
        ((("100", "kelvin"), ("10", "delta_degF")), ("1000", "kelvin*delta_degF")),
        ((("100", "degC"), ("10", "kelvin")), "error"),
        ((("100", "degC"), ("10", "degC")), "error"),
        ((("100", "degC"), ("10", "degF")), "error"),
        ((("100", "degC"), ("10", "degR")), "error"),
        ((("100", "degC"), ("10", "delta_degC")), "error"),
        ((("100", "degC"), ("10", "delta_degF")), "error"),
        ((("100", "degF"), ("10", "kelvin")), "error"),
        ((("100", "degF"), ("10", "degC")), "error"),
        ((("100", "degF"), ("10", "degF")), "error"),
        ((("100", "degF"), ("10", "degR")), "error"),
        ((("100", "degF"), ("10", "delta_degC")), "error"),
        ((("100", "degF"), ("10", "delta_degF")), "error"),
        ((("100", "degR"), ("10", "kelvin")), ("1000", "degR*kelvin")),
        ((("100", "degR"), ("10", "degC")), "error"),
        ((("100", "degR"), ("10", "degF")), "error"),
        ((("100", "degR"), ("10", "degR")), ("1000", "degR**2")),
        ((("100", "degR"), ("10", "delta_degC")), ("1000", "degR*delta_degC")),
        ((("100", "degR"), ("10", "delta_degF")), ("1000", "degR*delta_degF")),
        ((("100", "delta_degC"), ("10", "kelvin")), ("1000", "delta_degC*kelvin")),
        ((("100", "delta_degC"), ("10", "degC")), "error"),
        ((("100", "delta_degC"), ("10", "degF")), "error"),
        ((("100", "delta_degC"), ("10", "degR")), ("1000", "delta_degC*degR")),
        ((("100", "delta_degC"), ("10", "delta_degC")), ("1000", "delta_degC**2")),
        (
            (("100", "delta_degC"), ("10", "delta_degF")),
            ("1000", "delta_degC*delta_degF"),
        ),
        ((("100", "delta_degF"), ("10", "kelvin")), ("1000", "delta_degF*kelvin")),
        ((("100", "delta_degF"), ("10", "degC")), "error"),
        ((("100", "delta_degF"), ("10", "degF")), "error"),
        ((("100", "delta_degF"), ("10", "degR")), ("1000", "delta_degF*degR")),
        (
            (("100", "delta_degF"), ("10", "delta_degC")),
            ("1000", "delta_degF*delta_degC"),
        ),
        ((("100", "delta_degF"), ("10", "delta_degF")), ("1000", "delta_degF**2")),
    ]

    @ParameterizedTestCase.parameterize(("input", "expected_output"), multiplications)
    def test_multiplication(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = False
        qin1, qin2 = input_tuple
        q1, q2 = self.QP_(*qin1), self.QP_(*qin2)
        input_tuple = q1, q2
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.mul, q1, q2)
        else:
            expected = self.QP_(*expected)
            self.assertEqual(op.mul(q1, q2).units, expected.units)
            self.assertQuantityAlmostEqual(op.mul(q1, q2), expected, atol=0.01)

    divisions = [
        ((("100", "kelvin"), ("10", "kelvin")), ("10", "")),
        ((("100", "kelvin"), ("10", "degC")), "error"),
        ((("100", "kelvin"), ("10", "degF")), "error"),
        ((("100", "kelvin"), ("10", "degR")), ("10", "kelvin/degR")),
        ((("100", "kelvin"), ("10", "delta_degC")), ("10", "kelvin/delta_degC")),
        ((("100", "kelvin"), ("10", "delta_degF")), ("10", "kelvin/delta_degF")),
        ((("100", "degC"), ("10", "kelvin")), "error"),
        ((("100", "degC"), ("10", "degC")), "error"),
        ((("100", "degC"), ("10", "degF")), "error"),
        ((("100", "degC"), ("10", "degR")), "error"),
        ((("100", "degC"), ("10", "delta_degC")), "error"),
        ((("100", "degC"), ("10", "delta_degF")), "error"),
        ((("100", "degF"), ("10", "kelvin")), "error"),
        ((("100", "degF"), ("10", "degC")), "error"),
        ((("100", "degF"), ("10", "degF")), "error"),
        ((("100", "degF"), ("10", "degR")), "error"),
        ((("100", "degF"), ("10", "delta_degC")), "error"),
        ((("100", "degF"), ("10", "delta_degF")), "error"),
        ((("100", "degR"), ("10", "kelvin")), ("10", "degR/kelvin")),
        ((("100", "degR"), ("10", "degC")), "error"),
        ((("100", "degR"), ("10", "degF")), "error"),
        ((("100", "degR"), ("10", "degR")), ("10", "")),
        ((("100", "degR"), ("10", "delta_degC")), ("10", "degR/delta_degC")),
        ((("100", "degR"), ("10", "delta_degF")), ("10", "degR/delta_degF")),
        ((("100", "delta_degC"), ("10", "kelvin")), ("10", "delta_degC/kelvin")),
        ((("100", "delta_degC"), ("10", "degC")), "error"),
        ((("100", "delta_degC"), ("10", "degF")), "error"),
        ((("100", "delta_degC"), ("10", "degR")), ("10", "delta_degC/degR")),
        ((("100", "delta_degC"), ("10", "delta_degC")), ("10", "")),
        (
            (("100", "delta_degC"), ("10", "delta_degF")),
            ("10", "delta_degC/delta_degF"),
        ),
        ((("100", "delta_degF"), ("10", "kelvin")), ("10", "delta_degF/kelvin")),
        ((("100", "delta_degF"), ("10", "degC")), "error"),
        ((("100", "delta_degF"), ("10", "degF")), "error"),
        ((("100", "delta_degF"), ("10", "degR")), ("10", "delta_degF/degR")),
        (
            (("100", "delta_degF"), ("10", "delta_degC")),
            ("10", "delta_degF/delta_degC"),
        ),
        ((("100", "delta_degF"), ("10", "delta_degF")), ("10", "")),
    ]

    @ParameterizedTestCase.parameterize(("input", "expected_output"), divisions)
    def test_truedivision(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = False
        qin1, qin2 = input_tuple
        q1, q2 = self.QP_(*qin1), self.QP_(*qin2)
        input_tuple = q1, q2
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.truediv, q1, q2)
        else:
            expected = self.QP_(*expected)
            self.assertEqual(op.truediv(q1, q2).units, expected.units)
            self.assertQuantityAlmostEqual(op.truediv(q1, q2), expected, atol=0.01)

    multiplications_with_autoconvert_to_baseunit = [
        ((("100", "kelvin"), ("10", "degC")), ("28315.0", "kelvin**2")),
        ((("100", "kelvin"), ("10", "degF")), ("26092.78", "kelvin**2")),
        ((("100", "degC"), ("10", "kelvin")), ("3731.5", "kelvin**2")),
        ((("100", "degC"), ("10", "degC")), ("105657.42", "kelvin**2")),
        ((("100", "degC"), ("10", "degF")), ("97365.20", "kelvin**2")),
        ((("100", "degC"), ("10", "degR")), ("3731.5", "kelvin*degR")),
        ((("100", "degC"), ("10", "delta_degC")), ("3731.5", "kelvin*delta_degC")),
        ((("100", "degC"), ("10", "delta_degF")), ("3731.5", "kelvin*delta_degF")),
        ((("100", "degF"), ("10", "kelvin")), ("3109.28", "kelvin**2")),
        ((("100", "degF"), ("10", "degC")), ("88039.20", "kelvin**2")),
        ((("100", "degF"), ("10", "degF")), ("81129.69", "kelvin**2")),
        ((("100", "degF"), ("10", "degR")), ("3109.28", "kelvin*degR")),
        ((("100", "degF"), ("10", "delta_degC")), ("3109.28", "kelvin*delta_degC")),
        ((("100", "degF"), ("10", "delta_degF")), ("3109.28", "kelvin*delta_degF")),
        ((("100", "degR"), ("10", "degC")), ("28315.0", "degR*kelvin")),
        ((("100", "degR"), ("10", "degF")), ("26092.78", "degR*kelvin")),
        ((("100", "delta_degC"), ("10", "degC")), ("28315.0", "delta_degC*kelvin")),
        ((("100", "delta_degC"), ("10", "degF")), ("26092.78", "delta_degC*kelvin")),
        ((("100", "delta_degF"), ("10", "degC")), ("28315.0", "delta_degF*kelvin")),
        ((("100", "delta_degF"), ("10", "degF")), ("26092.78", "delta_degF*kelvin")),
    ]

    @ParameterizedTestCase.parameterize(
        ("input", "expected_output"), multiplications_with_autoconvert_to_baseunit
    )
    def test_multiplication_with_autoconvert(self, input_tuple, expected):
        self.ureg.autoconvert_offset_to_baseunit = True
        qin1, qin2 = input_tuple
        q1, q2 = self.QP_(*qin1), self.QP_(*qin2)
        input_tuple = q1, q2
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.mul, q1, q2)
        else:
            expected = self.QP_(*expected)
            self.assertEqual(op.mul(q1, q2).units, expected.units)
            self.assertQuantityAlmostEqual(op.mul(q1, q2), expected, atol=0.01)

    multiplications_with_scalar = [
        ((("10", "kelvin"), "2"), ("20.0", "kelvin")),
        ((("10", "kelvin**2"), "2"), ("20.0", "kelvin**2")),
        ((("10", "degC"), "2"), ("20.0", "degC")),
        ((("10", "1/degC"), "2"), "error"),
        ((("10", "degC**0.5"), "2"), "error"),
        ((("10", "degC**2"), "2"), "error"),
        ((("10", "degC**-2"), "2"), "error"),
    ]

    @ParameterizedTestCase.parameterize(
        ("input", "expected_output"), multiplications_with_scalar
    )
    def test_multiplication_with_scalar(self, input_tuple, expected):
        self.ureg.default_as_delta = False
        in1, in2 = input_tuple
        if type(in1) is tuple:
            in1, in2 = self.QP_(*in1), self.NON_INT_TYPE(in2)
        else:
            in1, in2 = in1, self.QP_(*in2)
        input_tuple = in1, in2  # update input_tuple for better tracebacks
        if expected == "error":
            self.assertRaises(OffsetUnitCalculusError, op.mul, in1, in2)
        else:
            expected = self.QP_(*expected)
            self.assertEqual(op.mul(in1, in2).units, expected.units)
            self.assertQuantityAlmostEqual(op.mul(in1, in2), expected, atol="0.01")

    divisions_with_scalar = [  # without / with autoconvert to base unit
        ((("10", "kelvin"), "2"), [("5.0", "kelvin"), ("5.0", "kelvin")]),
        ((("10", "kelvin**2"), "2"), [("5.0", "kelvin**2"), ("5.0", "kelvin**2")]),
        ((("10", "degC"), "2"), ["error", "error"]),
        ((("10", "degC**2"), "2"), ["error", "error"]),
        ((("10", "degC**-2"), "2"), ["error", "error"]),
        (("2", ("10", "kelvin")), [("0.2", "1/kelvin"), ("0.2", "1/kelvin")]),
        # (('2', ('10', "degC")), ["error", (2 / 283.15, "1/kelvin")]),
        (("2", ("10", "degC**2")), ["error", "error"]),
        (("2", ("10", "degC**-2")), ["error", "error"]),
    ]

    @ParameterizedTestCase.parameterize(
        ("input", "expected_output"), divisions_with_scalar
    )
    def test_division_with_scalar(self, input_tuple, expected):
        self.ureg.default_as_delta = False
        in1, in2 = input_tuple
        if type(in1) is tuple:
            in1, in2 = self.QP_(*in1), self.NON_INT_TYPE(in2)
        else:
            in1, in2 = self.NON_INT_TYPE(in1), self.QP_(*in2)
        input_tuple = in1, in2  # update input_tuple for better tracebacks
        expected_copy = expected[:]
        for i, mode in enumerate([False, True]):
            self.ureg.autoconvert_offset_to_baseunit = mode
            if expected_copy[i] == "error":
                self.assertRaises(OffsetUnitCalculusError, op.truediv, in1, in2)
            else:
                expected = self.QP_(*expected_copy[i])
                self.assertEqual(op.truediv(in1, in2).units, expected.units)
                self.assertQuantityAlmostEqual(op.truediv(in1, in2), expected)

    exponentiation = [  # resuls without / with autoconvert
        ((("10", "degC"), "1"), [("10", "degC"), ("10", "degC")]),
        # ((('10', "degC"), 0.5), ["error", (283.15 ** '0.5', "kelvin**0.5")]),
        ((("10", "degC"), "0"), [("1.0", ""), ("1.0", "")]),
        # ((('10', "degC"), -1), ["error", (1 / (10 + 273.15), "kelvin**-1")]),
        # ((('10', "degC"), -2), ["error", (1 / (10 + 273.15) ** 2.0, "kelvin**-2")]),
        # ((('0', "degC"), -2), ["error", (1 / (273.15) ** 2, "kelvin**-2")]),
        # ((('10', "degC"), ('2', "")), ["error", ((283.15) ** 2, "kelvin**2")]),
        ((("10", "degC"), ("10", "degK")), ["error", "error"]),
        (
            (("10", "kelvin"), ("2", "")),
            [("100.0", "kelvin**2"), ("100.0", "kelvin**2")],
        ),
        (("2", ("2", "kelvin")), ["error", "error"]),
        # (('2', ('500.0', "millikelvin/kelvin")), [2 ** 0.5, 2 ** 0.5]),
        # (('2', ('0.5', "kelvin/kelvin")), [2 ** 0.5, 2 ** 0.5]),
        # (
        #     (('10', "degC"), ('500.0', "millikelvin/kelvin")),
        #     ["error", (283.15 ** '0.5', "kelvin**0.5")],
        # ),
    ]

    @ParameterizedTestCase.parameterize(("input", "expected_output"), exponentiation)
    def test_exponentiation(self, input_tuple, expected):
        self.ureg.default_as_delta = False
        in1, in2 = input_tuple
        if type(in1) is tuple and type(in2) is tuple:
            in1, in2 = self.QP_(*in1), self.QP_(*in2)
        elif not type(in1) is tuple and type(in2) is tuple:
            in1, in2 = self.NON_INT_TYPE(in1), self.QP_(*in2)
        else:
            in1, in2 = self.QP_(*in1), self.NON_INT_TYPE(in2)
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
                    expected = self.QP_(*expected_copy[i])
                    self.assertEqual(op.pow(in1, in2).units, expected.units)
                else:
                    expected = expected_copy[i]
                self.assertQuantityAlmostEqual(op.pow(in1, in2), expected)


class NonIntTypeQuantityTestQuantityFloat(_TestBasic, NonIntTypeQuantityTestCase):

    NON_INT_TYPE = float


class NonIntTypeQuantityTestQuantityBasicMathFloat(
    _TestQuantityBasicMath, NonIntTypeQuantityTestCase
):

    NON_INT_TYPE = float


class NonIntTypeQuantityTestOffsetUnitMathFloat(
    _TestOffsetUnitMath, NonIntTypeQuantityTestCase
):

    NON_INT_TYPE = float


class NonIntTypeQuantityTestQuantityDecimal(_TestBasic, NonIntTypeQuantityTestCase):

    NON_INT_TYPE = Decimal


class NonIntTypeQuantityTestQuantityBasicMathDecimal(
    _TestQuantityBasicMath, NonIntTypeQuantityTestCase
):

    NON_INT_TYPE = Decimal


class NonIntTypeQuantityTestOffsetUnitMathDecimal(
    _TestOffsetUnitMath, NonIntTypeQuantityTestCase
):

    NON_INT_TYPE = Decimal


class NonIntTypeQuantityTestQuantityFraction(_TestBasic, NonIntTypeQuantityTestCase):

    NON_INT_TYPE = Fraction


class NonIntTypeQuantityTestQuantityBasicMathFraction(
    _TestQuantityBasicMath, NonIntTypeQuantityTestCase
):

    NON_INT_TYPE = Fraction


class NonIntTypeQuantityTestOffsetUnitMathFraction(
    _TestOffsetUnitMath, NonIntTypeQuantityTestCase
):

    NON_INT_TYPE = Fraction
