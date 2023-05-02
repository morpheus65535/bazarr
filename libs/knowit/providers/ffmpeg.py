
import json
import logging
import re
from logging import NullHandler, getLogger
from subprocess import check_output

from knowit import VIDEO_EXTENSIONS
from knowit.core import Property
from knowit.properties import (
    AudioChannels,
    AudioCodec,
    AudioProfile,
    Basic,
    Duration,
    Language,
    Quantity,
    Ratio,
    ScanType,
    SubtitleFormat,
    VideoCodec,
    VideoProfile,
    VideoProfileLevel,
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
from knowit.utils import (
    define_candidate,
    detect_os,
)

logger = getLogger(__name__)
logger.addHandler(NullHandler())


WARN_MSG = r'''
=========================================================================================
FFmpeg (ffprobe) not found on your system or could not be loaded.
Visit https://ffmpeg.org/download.html to download it.
If you still have problems, please check if the downloaded version matches your system.
To load FFmpeg (ffprobe) from a specific location, please define the location as follow:
  knowit --ffmpeg /usr/local/ffmpeg/bin <video_path>
  knowit --ffmpeg /usr/local/ffmpeg/bin/ffprobe <video_path>
  knowit --ffmpeg "C:\Program Files\FFmpeg" <video_path>
  knowit --ffmpeg C:\Software\ffprobe.exe <video_path>
=========================================================================================
'''


class FFmpegExecutor:
    """Executor that knows how to execute media info: using ctypes or cli."""

    version_re = re.compile(r'\bversion\s+(?P<version>[^\b\s]+)')
    locations = {
        'unix': ('/usr/local/ffmpeg/lib', '/usr/local/ffmpeg/bin', '__PATH__'),
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
        for exec_cls in (FFmpegCliExecutor, ):
            executor = exec_cls.create(os_family, suggested_path)
            if executor:
                return executor


class FFmpegCliExecutor(FFmpegExecutor):
    """Executor that uses FFmpeg (ffprobe) cli."""

    names = {
        'unix': ('ffprobe', ),
        'windows': ('ffprobe.exe', ),
        'macos': ('ffprobe', ),
    }

    def _execute(self, filename):
        return check_output([self.location, '-v', 'quiet', '-print_format', 'json',
                            '-show_format', '-show_streams', '-sexagesimal', filename]).decode()

    @classmethod
    def create(cls, os_family=None, suggested_path=None):
        """Create the executor instance."""
        for candidate in define_candidate(cls.locations, cls.names, os_family, suggested_path):
            try:
                output = check_output([candidate, '-version']).decode()
                version = cls._get_version(output)
                if version:
                    logger.debug('FFmpeg cli detected: %s v%s', candidate, version)
                    return FFmpegCliExecutor(candidate, version.split('.'))
            except OSError:
                pass


class FFmpegProvider(Provider):
    """FFmpeg provider."""

    def __init__(self, config, suggested_path=None):
        """Init method."""
        super().__init__(config, {
            'general': {
                'title': Property('tags.title', description='media title'),
                'path': Property('filename', description='media path'),
                'duration': Duration('duration', description='media duration'),
                'size': Quantity('size', unit=units.byte, description='media size'),
                'bit_rate': Quantity('bit_rate', unit=units.bps, description='media bit rate'),
            },
            'video': {
                'id': Basic('index', data_type=int, allow_fallback=True, description='video track number'),
                'name': Property('tags.title', description='video track name'),
                'language': Language('tags.language', description='video language'),
                'duration': Duration('duration', 'tags.duration', description='video duration'),
                'width': Quantity('width', unit=units.pixel),
                'height': Quantity('height', unit=units.pixel),
                'scan_type': ScanType(config, 'field_order', default='Progressive', description='video scan type'),
                'aspect_ratio': Ratio('display_aspect_ratio', description='display aspect ratio'),
                'pixel_aspect_ratio': Ratio('sample_aspect_ratio', description='pixel aspect ratio'),
                'resolution': None,  # populated with ResolutionRule
                'frame_rate': Ratio('r_frame_rate', unit=units.FPS, description='video frame rate'),
                # frame_rate_mode
                'bit_rate': Quantity('bit_rate', 'tags.bps', unit=units.bps, description='video bit rate'),
                'bit_depth': Quantity('bits_per_raw_sample', unit=units.bit, description='video bit depth'),
                'codec': VideoCodec(config, 'codec_name', description='video codec'),
                'profile': VideoProfile(config, 'profile', description='video codec profile'),
                'profile_level': VideoProfileLevel(config, 'level', description='video codec profile level'),
                # 'profile_tier': VideoProfileTier(config, 'codec_profile', description='video codec profile tier'),
                'forced': YesNo('disposition.forced', hide_value=False, description='video track forced'),
                'default': YesNo('disposition.default', hide_value=False, description='video track default'),
            },
            'audio': {
                'id': Basic('index', data_type=int, allow_fallback=True, description='audio track number'),
                'name': Property('tags.title', description='audio track name'),
                'language': Language('tags.language', description='audio language'),
                'duration': Duration('duration', 'tags.duration', description='audio duration'),
                'codec': AudioCodec(config, 'profile', 'codec_name', description='audio codec'),
                'profile': AudioProfile(config, 'profile', description='audio codec profile'),
                'channels_count': AudioChannels('channels', description='audio channels count'),
                'channels': None,  # populated with AudioChannelsRule
                'bit_depth': Quantity('bits_per_raw_sample', unit=units.bit, description='audio bit depth'),
                'bit_rate': Quantity('bit_rate', 'tags.bps', unit=units.bps, description='audio bit rate'),
                'sampling_rate': Quantity('sample_rate', unit=units.Hz, description='audio sampling rate'),
                'forced': YesNo('disposition.forced', hide_value=False, description='audio track forced'),
                'default': YesNo('disposition.default', hide_value=False, description='audio track default'),
            },
            'subtitle': {
                'id': Basic('index', data_type=int, allow_fallback=True, description='subtitle track number'),
                'name': Property('tags.title', description='subtitle track name'),
                'language': Language('tags.language', description='subtitle language'),
                'hearing_impaired': YesNo('disposition.hearing_impaired',
                                          hide_value=False, description='subtitle hearing impaired'),
                'closed_caption': None,  # populated with ClosedCaptionRule
                'format': SubtitleFormat(config, 'codec_name', description='subtitle format'),
                'forced': YesNo('disposition.forced', hide_value=False, description='subtitle track forced'),
                'default': YesNo('disposition.default', hide_value=False, description='subtitle track default'),
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
            },
        })
        self.executor = FFmpegExecutor.get_executor_instance(suggested_path)

    def accepts(self, video_path):
        """Accept any video when FFprobe is available."""
        if self.executor is None:
            logger.warning(WARN_MSG)
            self.executor = False

        return self.executor and video_path.lower().endswith(VIDEO_EXTENSIONS)

    def describe(self, video_path, context):
        """Return video metadata."""
        data = self.executor.extract_info(video_path)

        def debug_data():
            """Debug data."""
            return json.dumps(data, cls=get_json_encoder(context), indent=4, ensure_ascii=False)

        context['debug_data'] = debug_data

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Video %r scanned using ffmpeg %r has raw data:\n%s',
                         video_path, self.executor.location, debug_data())

        general_track = data.get('format') or {}
        if 'tags' in general_track:
            general_track['tags'] = {k.lower(): v for k, v in general_track['tags'].items()}

        video_tracks = []
        audio_tracks = []
        subtitle_tracks = []
        for track in data.get('streams'):
            track_type = track.get('codec_type')
            if track_type == 'video':
                video_tracks.append(track)
            elif track_type == 'audio':
                audio_tracks.append(track)
            elif track_type == 'subtitle':
                subtitle_tracks.append(track)

        result = self._describe_tracks(video_path, general_track, video_tracks, audio_tracks, subtitle_tracks, context)
        if not result:
            raise MalformedFileError

        result['provider'] = self.executor.location
        result['provider'] = {
            'name': 'ffmpeg',
            'version': self.version
        }

        return result

    @property
    def version(self):
        """Return ffmpeg version information."""
        if not self.executor:
            return {}
        version = '.'.join(map(str, self.executor.version))

        return {self.executor.location: f'v{version}'}
