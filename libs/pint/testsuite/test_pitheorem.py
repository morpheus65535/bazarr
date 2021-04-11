import itertools

from pint import pi_theorem
from pint.testsuite import QuantityTestCase


class TestPiTheorem(QuantityTestCase):

    FORCE_NDARRAY = False

    def test_simple(self):

        # simple movement
        with self.capture_log() as buffer:
            self.assertEqual(
                pi_theorem({"V": "m/s", "T": "s", "L": "m"}),
                [{"V": 1, "T": 1, "L": -1}],
            )

            # pendulum
            self.assertEqual(
                pi_theorem({"T": "s", "M": "grams", "L": "m", "g": "m/s**2"}),
                [{"g": 1, "T": 2, "L": -1}],
            )
            self.assertEqual(len(buffer), 7)

    def test_inputs(self):
        V = "km/hour"
        T = "ms"
        L = "cm"

        f1 = lambda x: x
        f2 = lambda x: self.Q_(1, x)
        f3 = lambda x: self.Q_(1, x).units
        f4 = lambda x: self.Q_(1, x).dimensionality

        fs = f1, f2, f3, f4
        for fv, ft, fl in itertools.product(fs, fs, fs):
            qv = fv(V)
            qt = ft(T)
            ql = ft(L)
            self.assertEqual(
                self.ureg.pi_theorem({"V": qv, "T": qt, "L": ql}),
                [{"V": 1.0, "T": 1.0, "L": -1.0}],
            )
