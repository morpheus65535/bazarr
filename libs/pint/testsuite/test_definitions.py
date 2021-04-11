from pint.converters import LogarithmicConverter, OffsetConverter, ScaleConverter
from pint.definitions import (
    AliasDefinition,
    Definition,
    DimensionDefinition,
    PrefixDefinition,
    UnitDefinition,
)
from pint.errors import DefinitionSyntaxError
from pint.testsuite import BaseTestCase
from pint.util import UnitsContainer


class TestDefinition(BaseTestCase):
    def test_invalid(self):
        with self.assertRaises(DefinitionSyntaxError):
            Definition.from_string("x = [time] * meter")
        with self.assertRaises(DefinitionSyntaxError):
            Definition.from_string("[x] = [time] * meter")

    def test_prefix_definition(self):

        self.assertRaises(ValueError, Definition.from_string, "m- = 1e-3 k")

        for definition in ("m- = 1e-3", "m- = 10**-3", "m- = 0.001"):
            x = Definition.from_string(definition)
            self.assertIsInstance(x, PrefixDefinition)
            self.assertEqual(x.name, "m")
            self.assertEqual(x.aliases, ())
            self.assertEqual(x.converter.to_reference(1000), 1)
            self.assertEqual(x.converter.from_reference(0.001), 1)
            self.assertEqual(str(x), "m")

        x = Definition.from_string("kilo- = 1e-3 = k-")
        self.assertIsInstance(x, PrefixDefinition)
        self.assertEqual(x.name, "kilo")
        self.assertEqual(x.aliases, ())
        self.assertEqual(x.symbol, "k")
        self.assertEqual(x.converter.to_reference(1000), 1)
        self.assertEqual(x.converter.from_reference(0.001), 1)

        x = Definition.from_string("kilo- = 1e-3 = k- = anotherk-")
        self.assertIsInstance(x, PrefixDefinition)
        self.assertEqual(x.name, "kilo")
        self.assertEqual(x.aliases, ("anotherk",))
        self.assertEqual(x.symbol, "k")
        self.assertEqual(x.converter.to_reference(1000), 1)
        self.assertEqual(x.converter.from_reference(0.001), 1)

    def test_baseunit_definition(self):
        x = Definition.from_string("meter = [length]")
        self.assertIsInstance(x, UnitDefinition)
        self.assertTrue(x.is_base)
        self.assertEqual(x.reference, UnitsContainer({"[length]": 1}))

    def test_unit_definition(self):
        x = Definition.from_string("coulomb = ampere * second")
        self.assertIsInstance(x, UnitDefinition)
        self.assertFalse(x.is_base)
        self.assertIsInstance(x.converter, ScaleConverter)
        self.assertEqual(x.converter.scale, 1)
        self.assertEqual(x.reference, UnitsContainer(ampere=1, second=1))

        x = Definition.from_string("faraday =  96485.3399 * coulomb")
        self.assertIsInstance(x, UnitDefinition)
        self.assertFalse(x.is_base)
        self.assertIsInstance(x.converter, ScaleConverter)
        self.assertEqual(x.converter.scale, 96485.3399)
        self.assertEqual(x.reference, UnitsContainer(coulomb=1))

        x = Definition.from_string("degF = 9 / 5 * kelvin; offset: 255.372222")
        self.assertIsInstance(x, UnitDefinition)
        self.assertFalse(x.is_base)
        self.assertIsInstance(x.converter, OffsetConverter)
        self.assertEqual(x.converter.scale, 9 / 5)
        self.assertEqual(x.converter.offset, 255.372222)
        self.assertEqual(x.reference, UnitsContainer(kelvin=1))

        x = Definition.from_string(
            "turn = 6.28 * radian = _ = revolution = = cycle = _"
        )
        self.assertIsInstance(x, UnitDefinition)
        self.assertEqual(x.name, "turn")
        self.assertEqual(x.aliases, ("revolution", "cycle"))
        self.assertEqual(x.symbol, "turn")
        self.assertFalse(x.is_base)
        self.assertIsInstance(x.converter, ScaleConverter)
        self.assertEqual(x.converter.scale, 6.28)
        self.assertEqual(x.reference, UnitsContainer(radian=1))

        self.assertRaises(
            ValueError,
            Definition.from_string,
            "degF = 9 / 5 * kelvin; offset: 255.372222 bla",
        )

    def test_log_unit_definition(self):

        x = Definition.from_string(
            "decibelmilliwatt = 1e-3 watt; logbase: 10; logfactor: 10 = dBm"
        )
        self.assertIsInstance(x, UnitDefinition)
        self.assertFalse(x.is_base)
        self.assertIsInstance(x.converter, LogarithmicConverter)
        self.assertEqual(x.converter.scale, 1e-3)
        self.assertEqual(x.converter.logbase, 10)
        self.assertEqual(x.converter.logfactor, 10)
        self.assertEqual(x.reference, UnitsContainer(watt=1))

        x = Definition.from_string("decibel = 1 ; logbase: 10; logfactor: 10 = dB")
        self.assertIsInstance(x, UnitDefinition)
        self.assertFalse(x.is_base)
        self.assertIsInstance(x.converter, LogarithmicConverter)
        self.assertEqual(x.converter.scale, 1)
        self.assertEqual(x.converter.logbase, 10)
        self.assertEqual(x.converter.logfactor, 10)
        self.assertEqual(x.reference, UnitsContainer())

        x = Definition.from_string("bell = 1 ; logbase: 10; logfactor: 1 = B")
        self.assertIsInstance(x, UnitDefinition)
        self.assertFalse(x.is_base)
        self.assertIsInstance(x.converter, LogarithmicConverter)
        self.assertEqual(x.converter.scale, 1)
        self.assertEqual(x.converter.logbase, 10)
        self.assertEqual(x.converter.logfactor, 1)
        self.assertEqual(x.reference, UnitsContainer())

        x = Definition.from_string("decade = 1 ; logbase: 10; logfactor: 1")
        self.assertIsInstance(x, UnitDefinition)
        self.assertFalse(x.is_base)
        self.assertIsInstance(x.converter, LogarithmicConverter)
        self.assertEqual(x.converter.scale, 1)
        self.assertEqual(x.converter.logbase, 10)
        self.assertEqual(x.converter.logfactor, 1)
        self.assertEqual(x.reference, UnitsContainer())

        eulersnumber = 2.71828182845904523536028747135266249775724709369995
        x = Definition.from_string(
            "neper = 1 ; logbase: %1.50f; logfactor: 0.5 = Np" % eulersnumber
        )
        self.assertIsInstance(x, UnitDefinition)
        self.assertFalse(x.is_base)
        self.assertIsInstance(x.converter, LogarithmicConverter)
        self.assertEqual(x.converter.scale, 1)
        self.assertEqual(x.converter.logbase, eulersnumber)
        self.assertEqual(x.converter.logfactor, 0.5)
        self.assertEqual(x.reference, UnitsContainer())

        x = Definition.from_string("octave = 1 ; logbase: 2; logfactor: 1 = oct")
        self.assertIsInstance(x, UnitDefinition)
        self.assertFalse(x.is_base)
        self.assertIsInstance(x.converter, LogarithmicConverter)
        self.assertEqual(x.converter.scale, 1)
        self.assertEqual(x.converter.logbase, 2)
        self.assertEqual(x.converter.logfactor, 1)
        self.assertEqual(x.reference, UnitsContainer())

    def test_dimension_definition(self):
        x = DimensionDefinition("[time]", "", (), None, is_base=True)
        self.assertTrue(x.is_base)
        self.assertEqual(x.name, "[time]")

        x = Definition.from_string("[speed] = [length]/[time]")
        self.assertIsInstance(x, DimensionDefinition)
        self.assertEqual(x.reference, UnitsContainer({"[length]": 1, "[time]": -1}))

    def test_alias_definition(self):
        x = Definition.from_string("@alias meter = metro = metr")
        self.assertIsInstance(x, AliasDefinition)
        self.assertEqual(x.name, "meter")
        self.assertEqual(x.aliases, ("metro", "metr"))
