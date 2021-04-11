import math

import pytest

from pint import OffsetUnitCalculusError, UnitRegistry
from pint.testsuite import QuantityTestCase
from pint.unit import Unit, UnitsContainer


@pytest.fixture(scope="module")
def auto_ureg():
    return UnitRegistry(autoconvert_offset_to_baseunit=True)


@pytest.fixture(scope="module")
def ureg():
    return UnitRegistry()


class TestLogarithmicQuantity(QuantityTestCase):

    FORCE_NDARRAY = False

    def test_log_quantity_creation(self):

        # Following Quantity Creation Pattern
        for args in (
            (4.2, "dBm"),
            (4.2, UnitsContainer(decibelmilliwatt=1)),
            (4.2, self.ureg.dBm),
        ):
            x = self.Q_(*args)
            self.assertEqual(x.magnitude, 4.2)
            self.assertEqual(x.units, UnitsContainer(decibelmilliwatt=1))

        x = self.Q_(self.Q_(4.2, "dBm"))
        self.assertEqual(x.magnitude, 4.2)
        self.assertEqual(x.units, UnitsContainer(decibelmilliwatt=1))

        x = self.Q_(4.2, UnitsContainer(decibelmilliwatt=1))
        y = self.Q_(x)
        self.assertEqual(x.magnitude, y.magnitude)
        self.assertEqual(x.units, y.units)
        self.assertIsNot(x, y)

        # Using multiplications for dB units requires autoconversion to baseunits
        new_reg = UnitRegistry(autoconvert_offset_to_baseunit=True)
        x = new_reg.Quantity("4.2 * dBm")
        self.assertEqual(x.magnitude, 4.2)
        self.assertEqual(x.units, UnitsContainer(decibelmilliwatt=1))

        with self.capture_log() as buffer:
            self.assertEqual(4.2 * new_reg.dBm, new_reg.Quantity(4.2, 2 * new_reg.dBm))
            self.assertEqual(len(buffer), 1)

    def test_log_convert(self):
        # # 1 dB = 1/10 * bel
        # self.assertQuantityAlmostEqual(self.Q_(1.0, "dB").to("dimensionless"), self.Q_(1, "bell") / 10)
        # # Uncomment Bell unit in default_en.txt

        # ## Test dB to dB units octave - decade
        # 1 decade = log2(10) octave
        self.assertQuantityAlmostEqual(
            self.Q_(1.0, "decade"), self.Q_(math.log(10, 2), "octave")
        )
        # ## Test dB to dB units dBm - dBu
        # 0 dBm = 1mW = 1e3 uW = 30 dBu
        self.assertAlmostEqual(self.Q_(0.0, "dBm"), self.Q_(29.999999999999996, "dBu"))

    def test_mix_regular_log_units(self):
        # Test regular-logarithmic mixed definition, such as dB/km or dB/cm

        # Multiplications and divisions with a mix of Logarithmic Units and regular Units is normally not possible.
        # The reason is that dB are considered by pint like offset units.
        # Multiplications and divisions that involve offset units are badly defined, so pint raises an error
        with self.assertRaises(OffsetUnitCalculusError):
            (-10.0 * self.ureg.dB) / (1 * self.ureg.cm)

        # However, if the flag autoconvert_offset_to_baseunit=True is given to UnitRegistry, then pint converts the unit to base.
        # With this flag on multiplications and divisions are now possible:
        new_reg = UnitRegistry(autoconvert_offset_to_baseunit=True)
        self.assertQuantityAlmostEqual(-10 * new_reg.dB / new_reg.cm, 0.1 / new_reg.cm)


log_unit_names = [
    "decibelmilliwatt",
    "dBm",
    "decibelmicrowatt",
    "dBu",
    "decibel",
    "dB",
    "decade",
    "octave",
    "oct",
]


@pytest.mark.parametrize("unit_name", log_unit_names)
def test_unit_by_attribute(ureg, unit_name):
    """Can the logarithmic units be accessed by attribute lookups?"""
    unit = getattr(ureg, unit_name)
    assert isinstance(unit, Unit)


@pytest.mark.parametrize("unit_name", log_unit_names)
def test_unit_parsing(ureg, unit_name):
    """Can the logarithmic units be understood by the parser?"""
    unit = ureg.parse_units(unit_name)
    assert isinstance(unit, Unit)


@pytest.mark.parametrize("mag", [1.0, 4.2])
@pytest.mark.parametrize("unit_name", log_unit_names)
def test_quantity_by_constructor(ureg, unit_name, mag):
    """Can Quantity() objects be constructed using logarithmic units?"""
    q = ureg.Quantity(mag, unit_name)
    assert q.magnitude == pytest.approx(mag)
    assert q.units == getattr(ureg, unit_name)


@pytest.mark.parametrize("mag", [1.0, 4.2])
@pytest.mark.parametrize("unit_name", log_unit_names)
def test_quantity_by_multiplication(auto_ureg, unit_name, mag):
    """Test that logarithmic units can be defined with multiplication

    Requires setting `autoconvert_offset_to_baseunit` to True
    """
    unit = getattr(auto_ureg, unit_name)
    q = mag * unit
    assert q.magnitude == pytest.approx(mag)
    assert q.units == unit


@pytest.mark.parametrize(
    "unit1,unit2",
    [
        ("decibelmilliwatt", "dBm"),
        ("decibelmicrowatt", "dBu"),
        ("decibel", "dB"),
        ("octave", "oct"),
    ],
)
def test_unit_equivalence(ureg, unit1, unit2):
    """Are certain pairs of units equivalent?"""
    assert getattr(ureg, unit1) == getattr(ureg, unit2)


@pytest.mark.parametrize(
    "db_value,scalar",
    [
        (0.0, 1.0),  # 0 dB == 1x
        (-10.0, 0.1),  # -10 dB == 0.1x
        (10.0, 10.0),
        (30.0, 1e3),
        (60.0, 1e6),
    ],
)
def test_db_conversion(ureg, db_value, scalar):
    """Test that a dB value can be converted to a scalar and back.
    """
    Q_ = ureg.Quantity
    assert Q_(db_value, "dB").to("dimensionless").magnitude == pytest.approx(scalar)
    assert Q_(scalar, "dimensionless").to("dB").magnitude == pytest.approx(db_value)


@pytest.mark.parametrize(
    "octave,scalar",
    [
        (2.0, 4.0),  # 2 octave == 4x
        (1.0, 2.0),  # 1 octave == 2x
        (0.0, 1.0),
        (-1.0, 0.5),
        (-2.0, 0.25),
    ],
)
def test_octave_conversion(ureg, octave, scalar):
    """Test that an octave can be converted to a scalar and back.
    """
    Q_ = ureg.Quantity
    assert Q_(octave, "octave").to("dimensionless").magnitude == pytest.approx(scalar)
    assert Q_(scalar, "dimensionless").to("octave").magnitude == pytest.approx(octave)


@pytest.mark.parametrize(
    "decade,scalar",
    [
        (2.0, 100.0),  # 2 decades == 100x
        (1.0, 10.0),  # 1 octave == 2x
        (0.0, 1.0),
        (-1.0, 0.1),
        (-2.0, 0.01),
    ],
)
def test_decade_conversion(ureg, decade, scalar):
    """Test that a decade can be converted to a scalar and back.
    """
    Q_ = ureg.Quantity
    assert Q_(decade, "decade").to("dimensionless").magnitude == pytest.approx(scalar)
    assert Q_(scalar, "dimensionless").to("decade").magnitude == pytest.approx(decade)


@pytest.mark.parametrize(
    "dbm_value,mw_value",
    [
        (0.0, 1.0),  # 0.0 dBm == 1.0 mW
        (10.0, 10.0),
        (20.0, 100.0),
        (-10.0, 0.1),
        (-20.0, 0.01),
    ],
)
def test_dbm_mw_conversion(ureg, dbm_value, mw_value):
    """Test dBm values can convert to mW and back.
    """
    Q_ = ureg.Quantity
    assert Q_(dbm_value, "dBm").to("mW").magnitude == pytest.approx(mw_value)
    assert Q_(mw_value, "mW").to("dBm").magnitude == pytest.approx(dbm_value)


@pytest.mark.xfail
def test_compound_log_unit_multiply_definition(auto_ureg):
    """Check that compound log units can be defined using multiply.
    """
    Q_ = auto_ureg.Quantity
    canonical_def = Q_(-161, "dBm") / auto_ureg.Hz
    mult_def = -161 * auto_ureg("dBm/Hz")
    assert mult_def == canonical_def


@pytest.mark.xfail
def test_compound_log_unit_quantity_definition(auto_ureg):
    """Check that compound log units can be defined using ``Quantity()``.
    """
    Q_ = auto_ureg.Quantity
    canonical_def = Q_(-161, "dBm") / auto_ureg.Hz
    quantity_def = Q_(-161, "dBm/Hz")
    assert quantity_def == canonical_def


def test_compound_log_unit_parse_definition(auto_ureg):
    Q_ = auto_ureg.Quantity
    canonical_def = Q_(-161, "dBm") / auto_ureg.Hz
    parse_def = auto_ureg("-161 dBm/Hz")
    assert parse_def == canonical_def


def test_compound_log_unit_parse_expr(auto_ureg):
    """Check that compound log units can be defined using ``parse_expression()``.
    """
    Q_ = auto_ureg.Quantity
    canonical_def = Q_(-161, "dBm") / auto_ureg.Hz
    parse_def = auto_ureg.parse_expression("-161 dBm/Hz")
    assert canonical_def == parse_def


@pytest.mark.xfail
def test_dbm_db_addition(auto_ureg):
    """Test a dB value can be added to a dBm and the answer is correct.
    """
    power = (5 * auto_ureg.dBm) + (10 * auto_ureg.dB)
    assert power.to("dBm").magnitude == pytest.approx(15)


@pytest.mark.xfail
@pytest.mark.parametrize(
    "freq1,octaves,freq2",
    [(100, 2.0, 400), (50, 1.0, 100), (200, 0.0, 200),],  # noqa: E231
)
def test_frequency_octave_addition(auto_ureg, freq1, octaves, freq2):
    """Test an Octave can be added to a frequency correctly
    """
    freq1 = freq1 * auto_ureg.Hz
    shift = octaves * auto_ureg.Octave
    new_freq = freq1 + shift
    assert new_freq.units == freq1.units
    assert new_freq.magnitude == pytest.approx(freq2)
