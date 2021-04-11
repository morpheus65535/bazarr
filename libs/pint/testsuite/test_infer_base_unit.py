from pint import Quantity as Q
from pint.testsuite import QuantityTestCase
from pint.util import infer_base_unit


class TestInferBaseUnit(QuantityTestCase):
    def test_infer_base_unit(self):
        from pint.util import infer_base_unit

        self.assertEqual(
            infer_base_unit(Q(1, "millimeter * nanometer")), Q(1, "meter**2").units
        )

    def test_units_adding_to_zero(self):
        self.assertEqual(infer_base_unit(Q(1, "m * mm / m / um * s")), Q(1, "s").units)

    def test_to_compact(self):
        r = Q(1000000000, "m") * Q(1, "mm") / Q(1, "s") / Q(1, "ms")
        compact_r = r.to_compact()
        expected = Q(1000.0, "kilometer**2 / second**2")
        self.assertQuantityAlmostEqual(compact_r, expected)

        r = (Q(1, "m") * Q(1, "mm") / Q(1, "m") / Q(2, "um") * Q(2, "s")).to_compact()
        self.assertQuantityAlmostEqual(r, Q(1000, "s"))

    def test_volts(self):
        from pint.util import infer_base_unit

        r = Q(1, "V") * Q(1, "mV") / Q(1, "kV")
        b = infer_base_unit(r)
        self.assertEqual(b, Q(1, "V").units)
        self.assertQuantityAlmostEqual(r, Q(1, "uV"))
