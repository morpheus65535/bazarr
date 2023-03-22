
import json
import logging
from collections import defaultdict
from logging import NullHandler, getLogger
import enzyme

from knowit.core import Property
from knowit.properties import (
    AudioCodec,
    Basic,
    Duration,
    Language,
    Quantity,
    VideoCodec,
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
from knowit.utils import to_dict

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class EnzymeProvider(Provider):
    """Enzyme Provider."""

    def __init__(self, config, *args, **kwargs):
        """Init method."""
        super().__init__(config, {
            'general': {
                'title': Property('title', description='media title'),
                'duration': Duration('duration', description='media duration'),
            },
            'video': {
                'id': Basic('number', data_type=int, description='video track number'),
                'name': Property('name', description='video track name'),
                'language': Language('language', description='video language'),
                'width': Quantity('width', unit=units.pixel),
                'height': Quantity('height', unit=units.pixel),
                'scan_type': YesNo('interlaced', yes='Interlaced', no='Progressive', default='Progressive',
                                   config=config, config_key='ScanType',
                                   description='video scan type'),
                'resolution': None,  # populated with ResolutionRule
                # 'bit_depth', Property('bit_depth', Integer('video bit depth')),
                'codec': VideoCodec(config, 'codec_id', description='video codec'),
                'forced': YesNo('forced', hide_value=False, description='video track forced'),
                'default': YesNo('default', hide_value=False, description='video track default'),
                'enabled': YesNo('enabled', hide_value=True, description='video track enabled'),
            },
            'audio': {
                'id': Basic('number', data_type=int, description='audio track number'),
                'name': Property('name', description='audio track name'),
                'language': Language('language', description='audio language'),
                'codec': AudioCodec(config, 'codec_id', description='audio codec'),
                'channels_count': Basic('channels', data_type=int, description='audio channels count'),
                'channels': None,  # populated with AudioChannelsRule
                'forced': YesNo('forced', hide_value=False, description='audio track forced'),
                'default': YesNo('default', hide_value=False, description='audio track default'),
                'enabled': YesNo('enabled', hide_value=True, description='audio track enabled'),
            },
            'subtitle': {
                'id': Basic('number', data_type=int, description='subtitle track number'),
                'name': Property('name', description='subtitle track name'),
                'language': Language('language', description='subtitle language'),
                'hearing_impaired': None,  # populated with HearingImpairedRule
                'closed_caption': None,  # populated with ClosedCaptionRule
                'forced': YesNo('forced', hide_value=False, description='subtitle track forced'),
                'default': YesNo('default', hide_value=False, description='subtitle track default'),
                'enabled': YesNo('enabled', hide_value=True, description='subtitle track enabled'),
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

    def accepts(self, video_path):
        """Accept only MKV files."""
        return video_path.lower().endswith('.mkv')

    @classmethod
    def extract_info(cls, video_path):
        """Extract info from the video."""
        with open(video_path, 'rb') as f:
            return to_dict(enzyme.MKV(f))

    def describe(self, video_path, context):
        """Return video metadata."""
        try:
            data = defaultdict(dict)
            ff = self.extract_info(video_path)

            def debug_data():
                """Debug data."""
                return json.dumps(ff, cls=get_json_encoder(context), indent=4, ensure_ascii=False)
            context['debug_data'] = debug_data

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('Video %r scanned using enzyme %r has raw data:\n%s',
                             video_path, enzyme.__version__, debug_data)

            data.update(ff)
            if 'info' in data and data['info'] is None:
                return {}
        except enzyme.MalformedMKVError:  # pragma: no cover
            raise MalformedFileError

        if logger.level == logging.DEBUG:
            logger.debug('Video {video_path} scanned using Enzyme {version} has raw data:\n{data}',
                         video_path=video_path, version=enzyme.__version__,
                         data=json.dumps(data, cls=get_json_encoder(context), indent=4, ensure_ascii=False))

        result = self._describe_tracks(video_path, data.get('info', {}), data.get('video_tracks'),
                                       data.get('audio_tracks'), data.get('subtitle_tracks'), context)

        if not result:
            raise MalformedFileError

        result['provider'] = {
            'name': 'enzyme',
            'version': self.version
        }

        return result

    @property
    def version(self):
        """Return enzyme version information."""
        return {'enzyme': enzyme.__version__}
