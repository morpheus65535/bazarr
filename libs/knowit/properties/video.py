import re
import typing
from decimal import Decimal

from knowit.core import Configurable, Property
from knowit.properties.general import Quantity
from knowit.utils import round_decimal


class VideoBitDepth(Quantity):
    """Video bit depth from a number or from a ffmpeg pixel format: yuv420p10le."""

    pix_fmt_re = re.compile(r'yuvj?\d+p(?P<bit_depth>\d+)?(?:le|be)?')

    def handle(self, value: typing.Any, context: typing.MutableMapping[str, typing.Any]) -> typing.Any:
        """Handle bit depth."""
        match = self.pix_fmt_re.fullmatch(value) if isinstance(value, str) else None
        if match:
            value = match['bit_depth'] or 8
        return super().handle(value, context)


class VideoCodec(Configurable[str]):
    """Video Codec handler."""

    @classmethod
    def _extract_key(cls, value: str) -> str:
        key = value.upper().split('/')[-1]
        if key.startswith('V_'):
            key = key[2:]

        return key.split(' ')[-1]


class VideoDimensions(Property[int]):
    """Dimensions property."""

    def __init__(self, *args: str, dimension: str = 'width', **kwargs: typing.Any):
        """Initialize the object."""
        super().__init__(*args, **kwargs)
        self.dimension = dimension

    dimensions_re = re.compile(r'(?P<width>\d+)x(?P<height>\d+)')

    def handle(self, value: typing.Any, context: typing.MutableMapping[str, typing.Any]) -> int | None:
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


class VideoEncoder(Configurable[str]):
    """Video Encoder property."""


class VideoHdrFormat(Configurable[str]):
    """Video HDR Format property."""


class VideoProfile(Configurable[str]):
    """Video Profile property."""

    @classmethod
    def _extract_key(cls, value: str) -> str:
        return value.upper().split('@')[0]


class VideoProfileLevel(Configurable[str]):
    """Video Profile Level property."""

    @classmethod
    def _extract_key(cls, value: str) -> str | typing.Literal[False]:
        values = str(value).upper().split('@')
        if len(values) > 1:
            return values[1]

        # There's no level, so don't warn or report it
        return False


class VideoProfileTier(Configurable[str]):
    """Video Profile Tier property."""

    @classmethod
    def _extract_key(cls, value: str) -> str | typing.Literal[False]:
        values = str(value).upper().split('@')
        if len(values) > 2:
            return values[2]

        # There's no tier, so don't warn or report it
        return False


class Ratio(Property[Decimal]):
    """Ratio property."""

    def __init__(self, *args: str, unit: typing.Any = None, **kwargs: typing.Any):
        """Initialize the object."""
        super().__init__(*args, **kwargs)
        self.unit = unit

    ratio_re = re.compile(r'(?P<width>\d+)[:/](?P<height>\d+)')

    def handle(self, value: typing.Any, context: typing.MutableMapping[str, typing.Any]) -> Decimal | None:
        """Handle ratio."""
        match = self.ratio_re.match(value)
        if match:
            width, height = match.groups()
            if (width, height) == ('0', '1'):  # identity
                return Decimal('1.0')

            if height:
                result = round_decimal(Decimal(width) / Decimal(height), min_digits=1, max_digits=3)
                if self.unit:
                    result *= self.unit

                return result

        self.report(value, context)
        return None


class ScanType(Configurable[str]):
    """Scan Type property."""
