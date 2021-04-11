import itertools

from pint.compat import np
from pint.converters import (
    Converter,
    LogarithmicConverter,
    OffsetConverter,
    ScaleConverter,
)
from pint.testsuite import BaseTestCase, helpers


class TestConverter(BaseTestCase):
    def test_converter(self):
        c = Converter()
        self.assertTrue(c.is_multiplicative)
        self.assertFalse(c.is_logarithmic)
        self.assertTrue(c.to_reference(8))
        self.assertTrue(c.from_reference(8))

    def test_multiplicative_converter(self):
        c = ScaleConverter(20.0)
        self.assertTrue(c.is_multiplicative)
        self.assertFalse(c.is_logarithmic)
        self.assertEqual(c.from_reference(c.to_reference(100)), 100)
        self.assertEqual(c.to_reference(c.from_reference(100)), 100)

    def test_offset_converter(self):
        c = OffsetConverter(20.0, 2)
        self.assertFalse(c.is_multiplicative)
        self.assertFalse(c.is_logarithmic)
        self.assertEqual(c.from_reference(c.to_reference(100)), 100)
        self.assertEqual(c.to_reference(c.from_reference(100)), 100)

    def test_log_converter(self):
        c = LogarithmicConverter(scale=1, logbase=10, logfactor=1)
        self.assertFalse(c.is_multiplicative)
        self.assertTrue(c.is_logarithmic)
        self.assertAlmostEqual(c.to_reference(0), 1)
        self.assertAlmostEqual(c.to_reference(1), 10)
        self.assertAlmostEqual(c.to_reference(2), 100)
        self.assertAlmostEqual(c.from_reference(1), 0)
        self.assertAlmostEqual(c.from_reference(10), 1)
        self.assertAlmostEqual(c.from_reference(100), 2)
        arb_value = 20.0
        self.assertAlmostEqual(c.from_reference(c.to_reference(arb_value)), arb_value)
        self.assertAlmostEqual(c.to_reference(c.from_reference(arb_value)), arb_value)

    @helpers.requires_numpy()
    def test_converter_inplace(self):
        for c in (ScaleConverter(20.0), OffsetConverter(20.0, 2)):
            fun1 = lambda x, y: c.from_reference(c.to_reference(x, y), y)
            fun2 = lambda x, y: c.to_reference(c.from_reference(x, y), y)
            for fun, (inplace, comp) in itertools.product(
                (fun1, fun2), ((True, self.assertIs), (False, self.assertIsNot))
            ):
                a = np.ones((1, 10))
                ac = np.ones((1, 10))
                r = fun(a, inplace)
                np.testing.assert_allclose(r, ac)
                comp(a, r)

    @helpers.requires_numpy()
    def test_log_converter_inplace(self):
        arb_value = 3.14
        c = LogarithmicConverter(scale=1, logbase=10, logfactor=1)

        from_to = lambda value, inplace: c.from_reference(
            c.to_reference(value, inplace), inplace
        )

        to_from = lambda value, inplace: c.to_reference(
            c.from_reference(value, inplace), inplace
        )

        for fun, (inplace, comp) in itertools.product(
            (from_to, to_from), ((True, self.assertIs), (False, self.assertIsNot))
        ):
            arb_array = arb_value * np.ones((1, 10))
            result = fun(arb_array, inplace)
            np.testing.assert_allclose(result, arb_array)
            comp(arb_array, result)
