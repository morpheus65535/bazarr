
from knowit.core import Configurable


class SubtitleFormat(Configurable[str]):
    """Subtitle Format property."""

    @classmethod
    def _extract_key(cls, value) -> str:
        key = str(value).upper()
        if key.startswith('S_'):
            key = key[2:]

        return key.split('/')[-1]
