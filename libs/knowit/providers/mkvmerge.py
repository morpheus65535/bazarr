import json
import logging
import re
import typing
from decimal import Decimal
from logging import NullHandler, getLogger
from subprocess import check_output

from knowit.config import Config
from knowit.core import Property
from knowit.properties import (
    AudioCodec,
    Basic,
    Duration,
    Language,
    Quantity,
    SubtitleFormat,
    VideoCodec,
    VideoDimensions,
    YesNo,
)
from knowit.provider import (
    Executor,
    MalformedFileError,
    NotFoundExecutor,
    Provider,
    run_command,
)
from knowit.rules import (
    AudioChannelsRule,
    ClosedCaptionRule,
    CommentaryRule,
    HearingImpairedRule,
    LanguageRule,
    ResolutionRule,
)
from knowit.rules.general import GuessTitleRule
from knowit.serializer import get_json_encoder
from knowit.units import units
from knowit.utils import OS_FAMILY, define_candidate, detect_os

logger = getLogger(__name__)
logger.addHandler(NullHandler())

WARN_MSG = r"""
=========================================================================================
mkvmerge not found on your system or could not be loaded.
Visit https://mkvtoolnix.download to download it.
If you still have problems, please check if the downloaded version matches your system.
To load mkvmerge from a specific location, please define the location as follow:
  knowit --mkvmerge /usr/local/mkvmerge/bin <video_path>
  knowit --mkvmerge /usr/local/mkvmerge/bin/ffprobe <video_path>
  knowit --mkvmerge "C:\Program Files\mkvmerge" <video_path>
  knowit --mkvmerge C:\Software\mkvmerge.exe <video_path>
=========================================================================================
"""


class MkvMergeExecutor(Executor):
    """Executor that knows how to execute mkvmerge."""

    version_re = re.compile(r'\bv(?P<version>[^\b\s]+)')
    locations = {
        'unix': ('/usr/local/mkvmerge/lib', '/usr/local/mkvmerge/bin', '__PATH__'),
        'windows': ('__PATH__',),
        'macos': ('__PATH__',),
    }

    def extract_info(self, filename: str) -> typing.Mapping[str, typing.Any]:
        """Extract media info."""
        json_dump = self._execute(filename)
        result: typing.Mapping[str, typing.Any] = json.loads(json_dump) if json_dump else {}
        return result

    def _execute(self, filename: str) -> str:
        raise NotImplementedError

    @classmethod
    def _get_version(cls, output: str) -> str | None:
        match = cls.version_re.search(output)
        if match:
            version = match.groupdict()['version']
            return version
        return None

    @classmethod
    def get_executor_instance(cls, suggested_path: str | None = None) -> 'MkvMergeExecutor | NotFoundExecutor':
        """Return executor instance."""
        os_family = detect_os()
        logger.debug('Detected os: %s', os_family)
        for exec_cls in (MkvMergeCliExecutor,):
            executor = exec_cls.create(os_family, suggested_path)
            if executor:
                return executor
        return NotFoundExecutor(suggested_path)


class MkvMergeCliExecutor(MkvMergeExecutor):
    """Executor that uses mkvmerge cli."""

    names = {
        'unix': ('mkvmerge',),
        'windows': ('mkvmerge.exe',),
        'macos': ('mkvmerge',),
    }

    def _execute(self, filename: str) -> str:
        assert self.location is not None
        return run_command([self.location, '-i', '-F', 'json', filename])

    @classmethod
    def create(
        cls, os_family: OS_FAMILY | None = None, suggested_path: str | None = None
    ) -> 'MkvMergeCliExecutor | None':
        """Create the executor instance."""
        for candidate in define_candidate(cls.locations, cls.names, os_family, suggested_path):
            try:
                output = check_output([candidate, '--version']).decode()
                version = cls._get_version(output)
                if version:
                    logger.debug('MkvMerge cli detected: %s v%s', candidate, version)
                    return MkvMergeCliExecutor(candidate, version.split('.'))
            except OSError:
                pass
        return None


class MkvMergeProvider(Provider):
    """MkvMerge Provider."""

    def __init__(self, config: Config, suggested_path: str | None = None, *args: typing.Any, **kwargs: typing.Any):
        """Init method."""
        super().__init__(
            config,
            {
                'general': {
                    'title': Property('title', description='media title'),
                    'duration': Duration('duration', resolution=Decimal('0.000001'), description='media duration'),
                },
                'video': {
                    'id': Basic('number', data_type=int, description='video track number'),
                    'name': Property('track_name', description='video track name'),
                    'language': Language('language_ietf', 'language', description='video language'),
                    'width': VideoDimensions('display_dimensions', dimension='width'),
                    'height': VideoDimensions('display_dimensions', dimension='height'),
                    'scan_type': YesNo(
                        'interlaced',
                        yes='Interlaced',
                        no='Progressive',
                        default='Progressive',
                        config=config,
                        config_key='ScanType',
                        description='video scan type',
                    ),
                    'resolution': None,  # populated with ResolutionRule
                    # 'bit_depth', Property('bit_depth', Integer('video bit depth')),
                    'codec': VideoCodec(config, 'codec_id', description='video codec'),
                    'forced': YesNo('forced_track', hide_value=False, description='video track forced'),
                    'default': YesNo('default_track', hide_value=False, description='video track default'),
                    'enabled': YesNo('enabled_track', hide_value=True, description='video track enabled'),
                },
                'audio': {
                    'id': Basic('number', data_type=int, description='audio track number'),
                    'name': Property('track_name', description='audio track name'),
                    'language': Language('language_ietf', 'language', description='audio language'),
                    'codec': AudioCodec(config, 'codec_id', description='audio codec'),
                    'channels_count': Basic('audio_channels', data_type=int, description='audio channels count'),
                    'channels': None,  # populated with AudioChannelsRule
                    'sampling_rate': Quantity(
                        'audio_sampling_frequency', unit=units.Hz, description='audio sampling rate'
                    ),
                    'commentary': YesNo('flag_commentary', hide_value=False, description='audio commentary'),
                    'forced': YesNo('forced_track', hide_value=False, description='audio track forced'),
                    'default': YesNo('default_track', hide_value=False, description='audio track default'),
                    'enabled': YesNo('enabled_track', hide_value=True, description='audio track enabled'),
                },
                'subtitle': {
                    'id': Basic('number', data_type=int, description='subtitle track number'),
                    'name': Property('track_name', description='subtitle track name'),
                    'language': Language('language_ietf', 'language', description='subtitle language'),
                    'hearing_impaired': YesNo(
                        'flag_hearing_impaired', hide_value=False, description='subtitle hearing impaired'
                    ),
                    'closed_caption': None,  # populated with ClosedCaptionRule
                    'format': SubtitleFormat(config, 'codec_id', description='subtitle format'),
                    'commentary': YesNo('flag_commentary', hide_value=False, description='subtitle commentary'),
                    'forced': YesNo('forced_track', hide_value=False, description='subtitle track forced'),
                    'default': YesNo('default_track', hide_value=False, description='subtitle track default'),
                    'enabled': YesNo('enabled_track', hide_value=True, description='subtitle track enabled'),
                },
            },
            {
                'video': {
                    'guessed': GuessTitleRule('guessed properties', private=True),
                    'language': LanguageRule('video language', override=True),
                    'resolution': ResolutionRule('video resolution'),
                },
                'audio': {
                    'guessed': GuessTitleRule('guessed properties', private=True),
                    'language': LanguageRule('audio language', override=True),
                    'commentary': CommentaryRule('audio commentary', override=True),
                    'channels': AudioChannelsRule('audio channels'),
                },
                'subtitle': {
                    'guessed': GuessTitleRule('guessed properties', private=True),
                    'language': LanguageRule('subtitle language', override=True),
                    'commentary': CommentaryRule('subtitle commentary', override=True),
                    'hearing_impaired': HearingImpairedRule('subtitle hearing impaired', override=True),
                    'closed_caption': ClosedCaptionRule('closed caption', override=True),
                },
            },
        )
        self.executor = MkvMergeExecutor.get_executor_instance(suggested_path)

    def loaded(self) -> bool:
        """If library or executable was found."""
        # if executor is None, print a warning and set to False to not repeat the warning
        if isinstance(self.executor, NotFoundExecutor) and not self.executor.warned:
            logger.warning(WARN_MSG)
            self.executor.warned = True
        # check if loaded
        return bool(self.executor)

    def accepts(self, video_path: str) -> bool:
        """Accept Matroska videos when mkvmerge is available."""
        return self.loaded() and video_path.lower().endswith(('.mkv', '.mka', '.mks'))

    @classmethod
    def extract_info(cls, video_path: str) -> typing.Any:
        """Extract info from the video."""
        return json.loads(check_output(['mkvmerge', '-i', '-F', video_path]).decode())

    def describe(
        self, video_path: str, context: typing.MutableMapping[str, typing.Any]
    ) -> typing.MutableMapping[str, typing.Any]:
        """Return video metadata."""
        if not self.loaded() or self.executor is None:
            return {}
        data = self.executor.extract_info(video_path)

        def debug_data() -> str:
            """Debug data."""
            return json.dumps(data, cls=get_json_encoder(context), indent=4, ensure_ascii=False)

        context['debug_data'] = debug_data

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                'Video %r scanned using mkvmerge %r has raw data:\n%s', video_path, self.executor.location, debug_data()
            )

        def merge_properties(target: typing.Mapping[str, typing.Any]) -> typing.Mapping[str, typing.Any]:
            """Merge properties sub properties into the target container."""
            return {**{k: v for k, v in target.items() if k != 'properties'}, **target.get('properties', {})}

        general_track = merge_properties(data.get('container', {}))
        video_tracks = []
        audio_tracks = []
        subtitle_tracks = []
        for track in data.get('tracks') or []:
            track_type = track.get('type')
            merged = merge_properties(track)
            if track_type == 'video':
                video_tracks.append(merged)
            elif track_type == 'audio':
                audio_tracks.append(merged)
            elif track_type == 'subtitles':
                subtitle_tracks.append(merged)

        result = self._describe_tracks(video_path, general_track, video_tracks, audio_tracks, subtitle_tracks, context)

        if not result:
            raise MalformedFileError

        result['provider'] = {'name': 'mkvmerge', 'version': self.version}

        return result

    @property
    def version(self) -> typing.Mapping[str, typing.Any]:
        """Return mkvmerge version information."""
        if not self.executor:
            return {}
        version = '.'.join(map(str, self.executor.version))

        return {self.executor.location or '': f'v{version}'}
