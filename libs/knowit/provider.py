import contextlib
import os
import subprocess
import typing
from logging import NullHandler, getLogger

import knowit.config
from knowit.core import Property, Rule
from knowit.properties import Quantity
from knowit.units import units
from knowit.utils import OS_FAMILY

logger = getLogger(__name__)
logger.addHandler(NullHandler())


size_property = Quantity('size', unit=units.byte, description='media size')

PropertyMap = typing.Mapping[str, Property[typing.Any] | None]
PropertyConfig = typing.Mapping[str, PropertyMap]

RuleMap = typing.Mapping[str, Rule[typing.Any]]
RuleConfig = typing.Mapping[str, RuleMap]


class Provider:
    """Base class for all providers."""

    executor: typing.Union['Executor', None]
    min_fps = 10
    max_fps = 200

    def __init__(
        self,
        config: knowit.config.Config,
        mapping: PropertyConfig,
        rules: RuleConfig | None = None,
    ):
        """Init method."""
        self.config = config
        self.mapping = mapping
        self.rules = rules or {}
        self.executor = None

    def loaded(self) -> bool:
        """Whether or not this provider was loaded."""
        raise NotImplementedError

    def accepts(self, target: str) -> bool:
        """Whether or not the video is supported by this provider."""
        raise NotImplementedError

    def describe(
        self, target: str, context: typing.MutableMapping[str, typing.Any]
    ) -> typing.MutableMapping[str, typing.Any]:
        """Read video metadata information."""
        raise NotImplementedError

    def _describe_tracks(
        self,
        video_path: str,
        general_track: typing.Mapping[str, typing.Any],
        video_tracks: typing.Iterable[typing.Mapping[str, typing.Any]] | None,
        audio_tracks: typing.Iterable[typing.Mapping[str, typing.Any]] | None,
        subtitle_tracks: typing.Iterable[typing.Mapping[str, typing.Any]] | None,
        context: typing.MutableMapping[str, typing.Any],
    ) -> typing.MutableMapping[str, typing.Any]:
        logger.debug('Handling general track')
        props = self._describe_track(general_track, 'general', context)

        if 'path' not in props:
            props['path'] = video_path
        if 'container' not in props:
            props['container'] = os.path.splitext(video_path)[1][1:]
        if 'size' not in props and os.path.isfile(video_path):
            props['size'] = size_property.handle(os.path.getsize(video_path), context)

        for (
            track_type,
            tracks,
        ) in (('video', video_tracks), ('audio', audio_tracks), ('subtitle', subtitle_tracks)):
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
    def _validate_track(
        cls, track_type: str, track: typing.MutableMapping[str, typing.Any]
    ) -> typing.MutableMapping[str, typing.Any] | None:
        if track_type != 'video' or 'frame_rate' not in track:
            return track

        frame_rate = track['frame_rate']
        with contextlib.suppress(AttributeError):
            frame_rate = frame_rate.magnitude

        if cls.min_fps < frame_rate < cls.max_fps:
            return track
        return None

    def _describe_track(
        self,
        track: typing.Mapping[str, typing.Any],
        track_type: str,
        context: typing.MutableMapping[str, typing.Any],
    ) -> typing.MutableMapping[str, typing.Any]:
        """Describe track to a dict.

        :param track:
        :param track_type:
        :rtype: dict
        """
        props: dict[str, typing.Any] = {}
        pv_props: dict[str, typing.Any] = {}
        for name, prop in self.mapping[track_type].items():
            if not prop:
                # placeholder to be populated by rules. It keeps the order
                props[name] = None
                continue

            value = prop.extract_value(track, context)
            if value is not None:
                which = props if not prop.private else pv_props
                which[name] = value

        for name, rule in self.rules.get(track_type, {}).items():
            if props.get(name) is not None and not rule.override:
                logger.debug('Skipping rule %s since property is already present: %r', name, props[name])
                continue

            value = rule.execute(props, pv_props, context)
            if value is not None:
                which = props if not rule.private else pv_props
                which[name] = value
            elif name in props and (not rule.override or props[name] is None):
                del props[name]

        return props

    def match_executor_location(self, suggested_path: str | None) -> bool:
        """Compare the suggested path to the path that was suggested when creating the provider."""
        if self.executor is None:
            return True
        return self.executor.location == suggested_path

    @property
    def version(self) -> typing.Mapping[str, typing.Any]:
        """Return provider version information."""
        raise NotImplementedError


class Executor:
    """Abstraction to a library or executable to be used by a provider."""

    def __init__(self, location: str | None, version: typing.Any):
        """Initialize the object."""
        self.location = location
        self.version = version

    def extract_info(self, filename: str) -> typing.Mapping[str, typing.Any]:
        """Extract media info."""
        raise NotImplementedError

    @classmethod
    def create(cls, os_family: OS_FAMILY | None = None, suggested_path: str | None = None) -> 'Executor | None':
        """Create the executor instance."""
        raise NotImplementedError

    @classmethod
    def get_executor_instance(cls, suggested_path: str | None = None) -> 'Executor':
        """Return executor instance."""
        raise NotImplementedError


class NotFoundExecutor(Executor):
    """Executor with a library or executable that was not found."""

    def __init__(self, location: str | None, version: typing.Any = None) -> None:
        """Initialize the object."""
        self.location = location
        self.warned = False

    def __bool__(self) -> bool:
        """Executor not found is always False."""
        return False

    def extract_info(self, filename: str) -> typing.Mapping[str, typing.Any]:
        """Extract media info."""
        return {}


class ProviderError(Exception):
    """Base class for provider exceptions."""

    pass


class MalformedFileError(ProviderError):
    """Malformed File error."""

    pass


class UnsupportedFileFormatError(ProviderError):
    """Unsupported File Format error."""

    pass


def run_command(args: list[str]) -> str:
    """Run a backend command and return its output. Keep the backend message when it fails."""
    process = subprocess.run(args, capture_output=True)
    if process.returncode:
        message = (process.stderr or process.stdout).decode(errors='replace').strip()
        raise ProviderError(f'{os.path.basename(args[0])} failed with exit status {process.returncode}: {message}')
    return process.stdout.decode()
