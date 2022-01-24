
import os
import typing
from logging import NullHandler, getLogger

import knowit.config
from knowit.core import Property, Rule
from knowit.properties import Quantity
from knowit.units import units

logger = getLogger(__name__)
logger.addHandler(NullHandler())


size_property = Quantity('size', unit=units.byte, description='media size')

PropertyMap = typing.Mapping[str, Property]
PropertyConfig = typing.Mapping[str, PropertyMap]

RuleMap = typing.Mapping[str, Rule]
RuleConfig = typing.Mapping[str, RuleMap]


class Provider:
    """Base class for all providers."""

    min_fps = 10
    max_fps = 200

    def __init__(
            self,
            config: knowit.config.Config,
            mapping: PropertyConfig,
            rules: typing.Optional[RuleConfig] = None,
    ):
        """Init method."""
        self.config = config
        self.mapping = mapping
        self.rules = rules or {}

    def accepts(self, target):
        """Whether or not the video is supported by this provider."""
        raise NotImplementedError

    def describe(self, target, context):
        """Read video metadata information."""
        raise NotImplementedError

    def _describe_tracks(self, video_path, general_track, video_tracks, audio_tracks, subtitle_tracks, context):
        logger.debug('Handling general track')
        props = self._describe_track(general_track, 'general', context)

        if 'path' not in props:
            props['path'] = video_path
        if 'container' not in props:
            props['container'] = os.path.splitext(video_path)[1][1:]
        if 'size' not in props and os.path.isfile(video_path):
            props['size'] = size_property.handle(os.path.getsize(video_path), context)

        for track_type, tracks, in (('video', video_tracks),
                                    ('audio', audio_tracks),
                                    ('subtitle', subtitle_tracks)):
            results = []
            for track in tracks or []:
                logger.debug('Handling %s track', track_type)
                t = self._validate_track(track_type, self._describe_track(track, track_type, context))
                if t:
                    results.append(t)

            if results:
                props[track_type] = results

        return props

    @classmethod
    def _validate_track(cls, track_type, track):
        if track_type != 'video' or 'frame_rate' not in track:
            return track

        frame_rate = track['frame_rate']
        try:
            frame_rate = frame_rate.magnitude
        except AttributeError:
            pass

        if cls.min_fps < frame_rate < cls.max_fps:
            return track

    def _describe_track(self, track, track_type, context):
        """Describe track to a dict.

        :param track:
        :param track_type:
        :rtype: dict
        """
        props = {}
        pv_props = {}
        for name, prop in self.mapping[track_type].items():
            if not prop:
                # placeholder to be populated by rules. It keeps the order
                props[name] = None
                continue

            value = prop.extract_value(track, context)
            if value is not None:
                if not prop.private:
                    which = props
                else:
                    which = pv_props
                which[name] = value

        for name, rule in self.rules.get(track_type, {}).items():
            if props.get(name) is not None and not rule.override:
                logger.debug('Skipping rule %s since property is already present: %r', name, props[name])
                continue

            value = rule.execute(props, pv_props, context)
            if value is not None:
                props[name] = value
            elif name in props and not rule.override:
                del props[name]

        return props

    @property
    def version(self):
        """Return provider version information."""
        raise NotImplementedError


class ProviderError(Exception):
    """Base class for provider exceptions."""

    pass


class MalformedFileError(ProviderError):
    """Malformed File error."""

    pass


class UnsupportedFileFormatError(ProviderError):
    """Unsupported File Format error."""

    pass
