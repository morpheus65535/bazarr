import re
import typing
from decimal import Decimal

from knowit.core import Configurable
from knowit.core import Property
from knowit.utils import round_decimal


class VideoCodec(Configurable[str]):
    """Video Codec handler."""

    @classmethod
    def _extract_key(cls, value) -> str:
        key = value.upper().split('/')[-1]
        if key.startswith('V_'):
            key = key[2:]

        return key.split(' ')[-1]


class VideoDimensions(Property[int]):
    """Dimensions property."""

    def __init__(self, *args: str, dimension='width' or 'height', **kwargs):
        """Initialize the object."""
        super().__init__(*args, **kwargs)
        self.dimension = dimension

    dimensions_re = re.compile(r'(?P<width>\d+)x(?P<height>\d+)')

    def handle(self, value, context) -> typing.Optional[int]:
        """Handle ratio."""
        match = self.dimensions_re.match(value)
        if match:
            match_dict = match.groupdict()
            try:
                value = match_dict[self.dimension]
            except KeyError:
                pass
            else:
                return int(value)

        self.report(value, context)
        return None


class VideoEncoder(Configurable):
    """Video Encoder property."""


class VideoHdrFormat(Configurable):
    """Video HDR Format property."""


class VideoProfile(Configurable[str]):
    """Video Profile property."""

    @classmethod
    def _extract_key(cls, value) -> str:
        return value.upper().split('@')[0]


class VideoProfileLevel(Configurable[str]):
    """Video Profile Level property."""

    @classmethod
    def _extract_key(cls, value) -> typing.Union[str, bool]:
        values = str(value).upper().split('@')
        if len(values) > 1:
            value = values[1]
            return value

        # There's no level, so don't warn or report it
        return False


class VideoProfileTier(Configurable[str]):
    """Video Profile Tier property."""

    @classmethod
    def _extract_key(cls, value) -> typing.Union[str, bool]:
        values = str(value).upper().split('@')
        if len(values) > 2:
            return values[2]

        # There's no tier, so don't warn or report it
        return False


class Ratio(Property[Decimal]):
    """Ratio property."""

    def __init__(self, *args: str, unit=None, **kwargs):
        """Initialize the object."""
        super().__init__(*args, **kwargs)
        self.unit = unit

    ratio_re = re.compile(r'(?P<width>\d+)[:/](?P<height>\d+)')

    def handle(self, value, context) -> typing.Optional[Decimal]:
        """Handle ratio."""
        match = self.ratio_re.match(value)
        if match:
            width, height = match.groups()
            if (width, height) == ('0', '1'):  # identity
                return Decimal('1.0')

            result = round_decimal(Decimal(width) / Decimal(height), min_digits=1, max_digits=3)
            if self.unit:
                result *= self.unit

            return result

        self.report(value, context)
        return None


class ScanType(Configurable[str]):
    """Scan Type property."""
