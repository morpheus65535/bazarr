from pint import formatting as fmt
from pint.testsuite import QuantityTestCase


class TestFormatter(QuantityTestCase):
    def test_join(self):
        for empty in (tuple(), []):
            self.assertEqual(fmt._join("s", empty), "")
        self.assertEqual(fmt._join("*", "1 2 3".split()), "1*2*3")
        self.assertEqual(fmt._join("{0}*{1}", "1 2 3".split()), "1*2*3")

    def test_formatter(self):
        self.assertEqual(fmt.formatter(dict().items()), "")
        self.assertEqual(fmt.formatter(dict(meter=1).items()), "meter")
        self.assertEqual(fmt.formatter(dict(meter=-1).items()), "1 / meter")
        self.assertEqual(
            fmt.formatter(dict(meter=-1).items(), as_ratio=False), "meter ** -1"
        )

        self.assertEqual(
            fmt.formatter(dict(meter=-1, second=-1).items(), as_ratio=False),
            "meter ** -1 * second ** -1",
        )
        self.assertEqual(
            fmt.formatter(dict(meter=-1, second=-1).items()), "1 / meter / second"
        )
        self.assertEqual(
            fmt.formatter(dict(meter=-1, second=-1).items(), single_denominator=True),
            "1 / (meter * second)",
        )
        self.assertEqual(
            fmt.formatter(dict(meter=-1, second=-2).items()), "1 / meter / second ** 2"
        )
        self.assertEqual(
            fmt.formatter(dict(meter=-1, second=-2).items(), single_denominator=True),
            "1 / (meter * second ** 2)",
        )

    def test_parse_spec(self):
        self.assertEqual(fmt._parse_spec(""), "")
        self.assertEqual(fmt._parse_spec(""), "")
        self.assertRaises(ValueError, fmt._parse_spec, "W")
        self.assertRaises(ValueError, fmt._parse_spec, "PL")

    def test_format_unit(self):
        self.assertEqual(fmt.format_unit("", "C"), "dimensionless")
        self.assertRaises(ValueError, fmt.format_unit, "m", "W")
