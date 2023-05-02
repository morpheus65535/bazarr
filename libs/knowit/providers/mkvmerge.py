
import json
import logging
import re
from decimal import Decimal
from logging import NullHandler, getLogger
from subprocess import check_output

from knowit.core import Property
from knowit.properties import (
    AudioCodec,
    Basic,
    Duration,
    Language,
    Quantity,
    VideoCodec,
    VideoDimensions,
    YesNo,
)
from knowit.provider import (
    MalformedFileError,
    Provider,
)
from knowit.rules import (
    AudioChannelsRule,
    ClosedCaptionRule,
    HearingImpairedRule,
    LanguageRule,
    ResolutionRule,
)
from knowit.rules.general import GuessTitleRule
from knowit.serializer import get_json_encoder
from knowit.units import units
from knowit.utils import define_candidate, detect_os

logger = getLogger(__name__)
logger.addHandler(NullHandler())

WARN_MSG = r'''
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
'''


class MkvMergeExecutor:
    """Executor that knows how to execute mkvmerge."""

    version_re = re.compile(r'\bv(?P<version>[^\b\s]+)')
    locations = {
        'unix': ('/usr/local/mkvmerge/lib', '/usr/local/mkvmerge/bin', '__PATH__'),
        'windows': ('__PATH__', ),
        'macos': ('__PATH__', ),
    }

    def __init__(self, location, version):
        """Initialize the object."""
        self.location = location
        self.version = version

    def extract_info(self, filename):
        """Extract media info."""
        json_dump = self._execute(filename)
        return json.loads(json_dump) if json_dump else {}

    def _execute(self, filename):
        raise NotImplementedError

    @classmethod
    def _get_version(cls, output):
        match = cls.version_re.search(output)
        if match:
            version = match.groupdict()['version']
            return version

    @classmethod
    def get_executor_instance(cls, suggested_path=None):
        """Return executor instance."""
        os_family = detect_os()
        logger.debug('Detected os: %s', os_family)
        for exec_cls in (MkvMergeCliExecutor, ):
            executor = exec_cls.create(os_family, suggested_path)
            if executor:
                return executor


class MkvMergeCliExecutor(MkvMergeExecutor):
    """Executor that uses mkvmerge cli."""

    names = {
        'unix': ('mkvmerge', ),
        'windows': ('mkvmerge.exe', ),
        'macos': ('mkvmerge', ),
    }

    def _execute(self, filename):
        return check_output([self.location, '-i', '-F', 'json', filename]).decode()

    @classmethod
    def create(cls, os_family=None, suggested_path=None):
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


class MkvMergeProvider(Provider):
    """MkvMerge Provider."""

    def __init__(self, config, suggested_path=None, *args, **kwargs):
        """Init method."""
        super().__init__(config, {
            'general': {
                'title': Property('title', description='media title'),
                'duration': Duration('duration', resolution=Decimal('0.000001'), description='media duration'),
            },
            'video': {
                'id': Basic('number', data_type=int, description='video track number'),
                'name': Property('name', description='video track name'),
                'language': Language('language_ietf', 'language', description='video language'),
                'width': VideoDimensions('display_dimensions', dimension='width'),
                'height': VideoDimensions('display_dimensions', dimension='height'),
                'scan_type': YesNo('interlaced', yes='Interlaced', no='Progressive', default='Progressive',
                                   config=config, config_key='ScanType',
                                   description='video scan type'),
                'resolution': None,  # populated with ResolutionRule
                # 'bit_depth', Property('bit_depth', Integer('video bit depth')),
                'codec': VideoCodec(config, 'codec_id', description='video codec'),
                'forced': YesNo('forced_track', hide_value=False, description='video track forced'),
                'default': YesNo('default_track', hide_value=False, description='video track default'),
                'enabled': YesNo('enabled_track', hide_value=True, description='video track enabled'),
            },
            'audio': {
                'id': Basic('number', data_type=int, description='audio track number'),
                'name': Property('name', description='audio track name'),
                'language': Language('language_ietf', 'language', description='audio language'),
                'codec': AudioCodec(config, 'codec_id', description='audio codec'),
                'channels_count': Basic('audio_channels', data_type=int, description='audio channels count'),
                'channels': None,  # populated with AudioChannelsRule
                'sampling_rate': Quantity('audio_sampling_frequency', unit=units.Hz, description='audio sampling rate'),
                'forced': YesNo('forced_track', hide_value=False, description='audio track forced'),
                'default': YesNo('default_track', hide_value=False, description='audio track default'),
                'enabled': YesNo('enabled_track', hide_value=True, description='audio track enabled'),
            },
            'subtitle': {
                'id': Basic('number', data_type=int, description='subtitle track number'),
                'name': Property('name', description='subtitle track name'),
                'language': Language('language_ietf', 'language', description='subtitle language'),
                'hearing_impaired': None,  # populated with HearingImpairedRule
                'closed_caption': None,  # populated with ClosedCaptionRule
                'forced': YesNo('forced_track', hide_value=False, description='subtitle track forced'),
                'default': YesNo('default_track', hide_value=False, description='subtitle track default'),
                'enabled': YesNo('enabled_track', hide_value=True, description='subtitle track enabled'),
            },
        }, {
            'video': {
                'guessed': GuessTitleRule('guessed properties', private=True),
                'language': LanguageRule('video language', override=True),
                'resolution': ResolutionRule('video resolution'),
            },
            'audio': {
                'guessed': GuessTitleRule('guessed properties', private=True),
                'language': LanguageRule('audio language', override=True),
                'channels': AudioChannelsRule('audio channels'),
            },
            'subtitle': {
                'guessed': GuessTitleRule('guessed properties', private=True),
                'language': LanguageRule('subtitle language', override=True),
                'hearing_impaired': HearingImpairedRule('subtitle hearing impaired', override=True),
                'closed_caption': ClosedCaptionRule('closed caption', override=True),
            }
        })
        self.executor = MkvMergeExecutor.get_executor_instance(suggested_path)

    def accepts(self, video_path):
        """Accept Matroska videos when mkvmerge is available."""
        if self.executor is None:
            logger.warning(WARN_MSG)
            self.executor = False

        return self.executor and video_path.lower().endswith(('.mkv', '.mka', '.mks'))

    @classmethod
    def extract_info(cls, video_path):
        """Extract info from the video."""
        return json.loads(check_output(['mkvmerge', '-i', '-F', video_path]).decode())

    def describe(self, video_path, context):
        """Return video metadata."""
        data = self.executor.extract_info(video_path)

        def debug_data():
            """Debug data."""
            return json.dumps(data, cls=get_json_encoder(context), indent=4, ensure_ascii=False)

        context['debug_data'] = debug_data

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Video %r scanned using mkvmerge %r has raw data:\n%s',
                         video_path, self.executor.location, debug_data())

        def merge_properties(target: dict):
            """Merge properties sub properties into the target container."""
            return {**{k: v for k, v in target.items() if k != 'properties'}, **target.get('properties', {})}

        general_track = merge_properties(data.get('container', {}))
        video_tracks = []
        audio_tracks = []
        subtitle_tracks = []
        for track in data.get('tracks'):
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

        result['provider'] = {
            'name': 'mkvmerge',
            'version': self.version
        }

        return result

    @property
    def version(self):
        """Return mkvmerge version information."""
        if not self.executor:
            return {}
        version = '.'.join(map(str, self.executor.version))

        return {self.executor.location: f'v{version}'}
