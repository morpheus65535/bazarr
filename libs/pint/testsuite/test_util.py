import collections
import copy
import math
import operator as op

from pint.testsuite import BaseTestCase, QuantityTestCase
from pint.util import (
    ParserHelper,
    UnitsContainer,
    find_connected_nodes,
    find_shortest_path,
    iterable,
    matrix_to_string,
    sized,
    string_preprocessor,
    to_units_container,
    tokenizer,
    transpose,
)


class TestUnitsContainer(QuantityTestCase):
    def _test_inplace(self, operator, value1, value2, expected_result):
        value1 = copy.copy(value1)
        value2 = copy.copy(value2)
        id1 = id(value1)
        id2 = id(value2)
        value1 = operator(value1, value2)
        value2_cpy = copy.copy(value2)
        self.assertEqual(value1, expected_result)
        # Inplace operation creates copies
        self.assertNotEqual(id1, id(value1))
        self.assertEqual(value2, value2_cpy)
        self.assertEqual(id2, id(value2))

    def _test_not_inplace(self, operator, value1, value2, expected_result):
        id1 = id(value1)
        id2 = id(value2)

        value1_cpy = copy.copy(value1)
        value2_cpy = copy.copy(value2)

        result = operator(value1, value2)

        self.assertEqual(expected_result, result)
        self.assertEqual(value1, value1_cpy)
        self.assertEqual(value2, value2_cpy)
        self.assertNotEqual(id(result), id1)
        self.assertNotEqual(id(result), id2)

    def test_unitcontainer_creation(self):
        x = UnitsContainer(meter=1, second=2)
        y = UnitsContainer({"meter": 1, "second": 2})
        self.assertIsInstance(x["meter"], int)
        self.assertEqual(x, y)
        self.assertIsNot(x, y)
        z = copy.copy(x)
        self.assertEqual(x, z)
        self.assertIsNot(x, z)
        z = UnitsContainer(x)
        self.assertEqual(x, z)
        self.assertIsNot(x, z)

    def test_unitcontainer_repr(self):
        x = UnitsContainer()
        self.assertEqual(str(x), "dimensionless")
        self.assertEqual(repr(x), "<UnitsContainer({})>")
        x = UnitsContainer(meter=1, second=2)
        self.assertEqual(str(x), "meter * second ** 2")
        self.assertEqual(repr(x), "<UnitsContainer({'meter': 1, 'second': 2})>")
        x = UnitsContainer(meter=1, second=2.5)
        self.assertEqual(str(x), "meter * second ** 2.5")
        self.assertEqual(repr(x), "<UnitsContainer({'meter': 1, 'second': 2.5})>")

    def test_unitcontainer_bool(self):
        self.assertTrue(UnitsContainer(meter=1, second=2))
        self.assertFalse(UnitsContainer())

    def test_unitcontainer_comp(self):
        x = UnitsContainer(meter=1, second=2)
        y = UnitsContainer(meter=1.0, second=2)
        z = UnitsContainer(meter=1, second=3)
        self.assertTrue(x == y)
        self.assertFalse(x != y)
        self.assertFalse(x == z)
        self.assertTrue(x != z)

    def test_unitcontainer_arithmetic(self):
        x = UnitsContainer(meter=1)
        y = UnitsContainer(second=1)
        z = UnitsContainer(meter=1, second=-2)

        self._test_not_inplace(op.mul, x, y, UnitsContainer(meter=1, second=1))
        self._test_not_inplace(op.truediv, x, y, UnitsContainer(meter=1, second=-1))
        self._test_not_inplace(op.pow, z, 2, UnitsContainer(meter=2, second=-4))
        self._test_not_inplace(op.pow, z, -2, UnitsContainer(meter=-2, second=4))

        self._test_inplace(op.imul, x, y, UnitsContainer(meter=1, second=1))
        self._test_inplace(op.itruediv, x, y, UnitsContainer(meter=1, second=-1))
        self._test_inplace(op.ipow, z, 2, UnitsContainer(meter=2, second=-4))
        self._test_inplace(op.ipow, z, -2, UnitsContainer(meter=-2, second=4))

    def test_string_comparison(self):
        x = UnitsContainer(meter=1)
        y = UnitsContainer(second=1)
        z = UnitsContainer(meter=1, second=-2)
        self.assertEqual(x, "meter")
        self.assertEqual("meter", x)
        self.assertNotEqual(x, "meter ** 2")
        self.assertNotEqual(x, "meter * meter")
        self.assertNotEqual(x, "second")
        self.assertEqual(y, "second")
        self.assertEqual(z, "meter/second/second")

    def test_invalid(self):
        self.assertRaises(TypeError, UnitsContainer, {1: 2})
        self.assertRaises(TypeError, UnitsContainer, {"1": "2"})
        d = UnitsContainer()
        self.assertRaises(TypeError, d.__mul__, list())
        self.assertRaises(TypeError, d.__pow__, list())
        self.assertRaises(TypeError, d.__truediv__, list())
        self.assertRaises(TypeError, d.__rtruediv__, list())


class TestToUnitsContainer(BaseTestCase):
    def test_str_conversion(self):
        self.assertEqual(to_units_container("m"), UnitsContainer(m=1))

    def test_uc_conversion(self):
        a = UnitsContainer(m=1)
        self.assertIs(to_units_container(a), a)

    def test_quantity_conversion(self):
        from pint.registry import UnitRegistry

        ureg = UnitRegistry()
        self.assertEqual(
            to_units_container(ureg.Quantity(1, UnitsContainer(m=1))),
            UnitsContainer(m=1),
        )

    def test_unit_conversion(self):
        from pint import Unit

        self.assertEqual(
            to_units_container(Unit(UnitsContainer(m=1))), UnitsContainer(m=1)
        )

    def test_dict_conversion(self):
        self.assertEqual(to_units_container(dict(m=1)), UnitsContainer(m=1))


class TestParseHelper(BaseTestCase):
    def test_basic(self):
        # Parse Helper ar mutables, so we build one everytime
        x = lambda: ParserHelper(1, meter=2)
        xp = lambda: ParserHelper(1, meter=2)
        y = lambda: ParserHelper(2, meter=2)

        self.assertEqual(x(), xp())
        self.assertNotEqual(x(), y())
        self.assertEqual(ParserHelper.from_string(""), ParserHelper())
        self.assertEqual(repr(x()), "<ParserHelper(1, {'meter': 2})>")

        self.assertEqual(ParserHelper(2), 2)

        self.assertEqual(x(), dict(meter=2))
        self.assertEqual(x(), "meter ** 2")
        self.assertNotEqual(y(), dict(meter=2))
        self.assertNotEqual(y(), "meter ** 2")

        self.assertNotEqual(xp(), object())

    def test_calculate(self):
        # Parse Helper ar mutables, so we build one everytime
        x = lambda: ParserHelper(1.0, meter=2)
        y = lambda: ParserHelper(2.0, meter=-2)
        z = lambda: ParserHelper(2.0, meter=2)

        self.assertEqual(x() * 4.0, ParserHelper(4.0, meter=2))
        self.assertEqual(x() * y(), ParserHelper(2.0))
        self.assertEqual(x() * "second", ParserHelper(1.0, meter=2, second=1))

        self.assertEqual(x() / 4.0, ParserHelper(0.25, meter=2))
        self.assertEqual(x() / "second", ParserHelper(1.0, meter=2, second=-1))
        self.assertEqual(x() / z(), ParserHelper(0.5))

        self.assertEqual(4.0 / z(), ParserHelper(2.0, meter=-2))
        self.assertEqual("seconds" / z(), ParserHelper(0.5, seconds=1, meter=-2))
        self.assertEqual(dict(seconds=1) / z(), ParserHelper(0.5, seconds=1, meter=-2))

    def _test_eval_token(self, expected, expression, use_decimal=False):
        token = next(tokenizer(expression))
        actual = ParserHelper.eval_token(token, use_decimal=use_decimal)
        self.assertEqual(expected, actual)
        self.assertEqual(type(expected), type(actual))

    def test_eval_token(self):
        self._test_eval_token(1000.0, "1e3")
        self._test_eval_token(1000.0, "1E3")
        self._test_eval_token(1000, "1000")

    def test_nan(self):
        for s in ("nan", "NAN", "NaN", "123 NaN nan NAN 456"):
            with self.subTest(s):
                p = ParserHelper.from_string(s + " kg")
                assert math.isnan(p.scale)
                self.assertEqual(dict(p), {"kg": 1})


class TestStringProcessor(BaseTestCase):
    def _test(self, bef, aft):
        for pattern in ("{}", "+{}+"):
            b = pattern.format(bef)
            a = pattern.format(aft)
            self.assertEqual(string_preprocessor(b), a)

    def test_square_cube(self):
        self._test("bcd^3", "bcd**3")
        self._test("bcd^ 3", "bcd** 3")
        self._test("bcd ^3", "bcd **3")
        self._test("bcd squared", "bcd**2")
        self._test("bcd squared", "bcd**2")
        self._test("bcd cubed", "bcd**3")
        self._test("sq bcd", "bcd**2")
        self._test("square bcd", "bcd**2")
        self._test("cubic bcd", "bcd**3")
        self._test("bcd efg", "bcd*efg")

    def test_per(self):
        self._test("miles per hour", "miles/hour")

    def test_numbers(self):
        self._test("1,234,567", "1234567")
        self._test("1e-24", "1e-24")
        self._test("1e+24", "1e+24")
        self._test("1e24", "1e24")
        self._test("1E-24", "1E-24")
        self._test("1E+24", "1E+24")
        self._test("1E24", "1E24")

    def test_space_multiplication(self):
        self._test("bcd efg", "bcd*efg")
        self._test("bcd  efg", "bcd*efg")
        self._test("1 hour", "1*hour")
        self._test("1. hour", "1.*hour")
        self._test("1.1 hour", "1.1*hour")
        self._test("1E24 hour", "1E24*hour")
        self._test("1E-24 hour", "1E-24*hour")
        self._test("1E+24 hour", "1E+24*hour")
        self._test("1.2E24 hour", "1.2E24*hour")
        self._test("1.2E-24 hour", "1.2E-24*hour")
        self._test("1.2E+24 hour", "1.2E+24*hour")

    def test_joined_multiplication(self):
        self._test("1hour", "1*hour")
        self._test("1.hour", "1.*hour")
        self._test("1.1hour", "1.1*hour")
        self._test("1h", "1*h")
        self._test("1.h", "1.*h")
        self._test("1.1h", "1.1*h")

    def test_names(self):
        self._test("g_0", "g_0")
        self._test("g0", "g0")
        self._test("g", "g")
        self._test("water_60F", "water_60F")


class TestGraph(BaseTestCase):
    def test_start_not_in_graph(self):
        g = collections.defaultdict(set)
        g[1] = {2}
        g[2] = {3}
        self.assertIs(find_connected_nodes(g, 9), None)

    def test_shortest_path(self):
        g = collections.defaultdict(set)
        g[1] = {2}
        g[2] = {3}
        p = find_shortest_path(g, 1, 2)
        self.assertEqual(p, [1, 2])
        p = find_shortest_path(g, 1, 3)
        self.assertEqual(p, [1, 2, 3])
        p = find_shortest_path(g, 3, 1)
        self.assertIs(p, None)

        g = collections.defaultdict(set)
        g[1] = {2}
        g[2] = {3, 1}
        g[3] = {2}
        p = find_shortest_path(g, 1, 2)
        self.assertEqual(p, [1, 2])
        p = find_shortest_path(g, 1, 3)
        self.assertEqual(p, [1, 2, 3])
        p = find_shortest_path(g, 3, 1)
        self.assertEqual(p, [3, 2, 1])
        p = find_shortest_path(g, 2, 1)
        self.assertEqual(p, [2, 1])


class TestMatrix(BaseTestCase):
    def test_matrix_to_string(self):

        self.assertEqual(
            matrix_to_string([[1, 2], [3, 4]], row_headers=None, col_headers=None),
            "1\t2\n" "3\t4",
        )

        self.assertEqual(
            matrix_to_string(
                [[1, 2], [3, 4]],
                row_headers=None,
                col_headers=None,
                fmtfun=lambda x: f"{x:.2f}",
            ),
            "1.00\t2.00\n" "3.00\t4.00",
        )

        self.assertEqual(
            matrix_to_string(
                [[1, 2], [3, 4]], row_headers=["c", "d"], col_headers=None
            ),
            "c\t1\t2\n" "d\t3\t4",
        )

        self.assertEqual(
            matrix_to_string(
                [[1, 2], [3, 4]], row_headers=None, col_headers=["a", "b"]
            ),
            "a\tb\n" "1\t2\n" "3\t4",
        )

        self.assertEqual(
            matrix_to_string(
                [[1, 2], [3, 4]], row_headers=["c", "d"], col_headers=["a", "b"]
            ),
            "\ta\tb\n" "c\t1\t2\n" "d\t3\t4",
        )

    def test_transpose(self):

        self.assertEqual(transpose([[1, 2], [3, 4]]), [[1, 3], [2, 4]])


class TestOtherUtils(BaseTestCase):
    def test_iterable(self):

        # Test with list, string, generator, and scalar
        self.assertTrue(iterable([0, 1, 2, 3]))
        self.assertTrue(iterable("test"))
        self.assertTrue(iterable((i for i in range(5))))
        self.assertFalse(iterable(0))

    def test_sized(self):

        # Test with list, string, generator, and scalar
        self.assertTrue(sized([0, 1, 2, 3]))
        self.assertTrue(sized("test"))
        self.assertFalse(sized((i for i in range(5))))
        self.assertFalse(sized(0))
