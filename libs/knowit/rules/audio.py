import typing
from decimal import Decimal, InvalidOperation
from logging import NullHandler, getLogger

from knowit.core import Rule

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class AtmosRule(Rule):
    """Atmos rule."""

    def __init__(self, config: typing.Mapping[str, typing.Mapping], name: str,
                 **kwargs):
        """Initialize an Atmos rule."""
        super().__init__(name, **kwargs)
        self.audio_codecs = getattr(config, 'AudioCodec')

    def execute(self, props, pv_props, context):
        """Execute the rule against properties."""
        profile = context.get('profile') or 'default'
        format_commercial = pv_props.get('format_commercial')
        if 'codec' in props and format_commercial and 'atmos' in format_commercial.lower():
            props['codec'] = [props['codec'],
                              getattr(self.audio_codecs['ATMOS'], profile)]


class AudioChannelsRule(Rule):
    """Audio Channel rule."""

    mapping = {
        1: '1.0',
        2: '2.0',
        6: '5.1',
        8: '7.1',
    }

    def execute(self, props, pv_props, context):
        """Execute the rule against properties."""
        count = props.get('channels_count')
        if count is None:
            return

        channels = self.mapping.get(count) if isinstance(count, int) else None
        positions = pv_props.get('channel_positions') or []
        positions = positions if isinstance(positions, list) else [positions]
        candidate = 0
        for position in positions:
            if not position:
                continue

            c = Decimal('0.0')
            for i in position.split('/'):
                try:
                    c += Decimal(i.replace('.?', ''))
                except (ValueError, InvalidOperation):
                    logger.debug('Invalid %s: %s', self.description, i)
                    pass

            c_count = int(c) + int(round((c - int(c)) * 10))
            if c_count == count:
                return str(c)

            candidate = max(candidate, c)

        if channels:
            return channels

        if candidate:
            return candidate

        self.report(positions, context)


class DtsHdRule(Rule):
    """DTS-HD rule."""

    def __init__(self, config: typing.Mapping[str, typing.Mapping], name: str,
                 **kwargs):
        """Initialize a DTS-HD Rule."""
        super().__init__(name, **kwargs)
        self.audio_codecs = getattr(config, 'AudioCodec')
        self.audio_profiles = getattr(config, 'AudioProfile')

    @classmethod
    def _redefine(cls, props, name, index):
        actual = props.get(name)
        if isinstance(actual, list):
            value = actual[index]
            if value is None:
                del props[name]
            else:
                props[name] = value

    def execute(self, props, pv_props, context):
        """Execute the rule against properties."""
        profile = context.get('profile') or 'default'

        if props.get('codec') == getattr(self.audio_codecs['DTS'],
                                         profile) and props.get('profile') in (
                getattr(self.audio_profiles['MA'], profile),
                getattr(self.audio_profiles['HRA'], profile)):
            props['codec'] = getattr(self.audio_codecs['DTS-HD'], profile)
