import typing

from knowit.core import Configurable, Property


class BitRateMode(Configurable[str]):
    """Bit Rate mode property."""


class AudioCompression(Configurable[str]):
    """Audio Compression property."""


class AudioProfile(Configurable[str]):
    """Audio profile property."""


class AudioChannels(Property[int]):
    """Audio Channels property."""

    ignored = {
        'object based',  # Dolby Atmos
    }

    def handle(self, value: typing.Union[int, str], context: typing.MutableMapping) -> typing.Optional[int]:
        """Handle audio channels."""
        if isinstance(value, int):
            return value

        if value.lower() not in self.ignored:
            try:
                return int(value)
            except ValueError:
                self.report(value, context)
        return None


class AudioCodec(Configurable[str]):
    """Audio codec property."""

    @classmethod
    def _extract_key(cls, value) -> str:
        key = str(value).upper()
        if key.startswith('A_'):
            key = key[2:]

        # only the first part of the word. E.g.: 'AAC LC' => 'AAC'
        return key.split(' ')[0]

    @classmethod
    def _extract_fallback_key(cls, value, key) -> typing.Optional[str]:
        if '/' in key:
            return key.split('/')[0]
        else:
            return None
