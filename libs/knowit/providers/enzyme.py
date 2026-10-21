import json
import logging
import typing
from collections import defaultdict
from logging import NullHandler, getLogger

import enzyme

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
    YesNo,
)
from knowit.provider import (
    MalformedFileError,
    Provider,
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
from knowit.utils import to_dict

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class EnzymeProvider(Provider):
    """Enzyme Provider."""

    def __init__(self, config: Config, *args: typing.Any, **kwargs: typing.Any):
        """Init method."""
        super().__init__(
            config,
            {
                'general': {
                    'title': Property('title', description='media title'),
                    'duration': Duration('duration', description='media duration'),
                },
                'video': {
                    'id': Basic('number', data_type=int, description='video track number'),
                    'name': Property('name', description='video track name'),
                    # Matroska default (RFC 9559). enzyme does not read LanguageBCP47, which overrides it.
                    'language': Language('language', default='eng', description='video language'),
                    'width': Quantity('width', unit=units.pixel),
                    'height': Quantity('height', unit=units.pixel),
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
                    'forced': YesNo('forced', hide_value=False, description='video track forced'),
                    'default': YesNo('default', hide_value=False, description='video track default'),
                    'enabled': YesNo('enabled', hide_value=True, description='video track enabled'),
                },
                'audio': {
                    'id': Basic('number', data_type=int, description='audio track number'),
                    'name': Property('name', description='audio track name'),
                    'language': Language('language', default='eng', description='audio language'),
                    'codec': AudioCodec(config, 'codec_id', description='audio codec'),
                    'channels_count': Basic('channels', data_type=int, description='audio channels count'),
                    'channels': None,  # populated with AudioChannelsRule
                    'commentary': None,  # populated with CommentaryRule
                    'forced': YesNo('forced', hide_value=False, description='audio track forced'),
                    'default': YesNo('default', hide_value=False, description='audio track default'),
                    'enabled': YesNo('enabled', hide_value=True, description='audio track enabled'),
                },
                'subtitle': {
                    'id': Basic('number', data_type=int, description='subtitle track number'),
                    'name': Property('name', description='subtitle track name'),
                    'language': Language('language', default='eng', description='subtitle language'),
                    'hearing_impaired': None,  # populated with HearingImpairedRule
                    'closed_caption': None,  # populated with ClosedCaptionRule
                    'format': SubtitleFormat(config, 'codec_id', description='subtitle format'),
                    'commentary': None,  # populated with CommentaryRule
                    'forced': YesNo('forced', hide_value=False, description='subtitle track forced'),
                    'default': YesNo('default', hide_value=False, description='subtitle track default'),
                    'enabled': YesNo('enabled', hide_value=True, description='subtitle track enabled'),
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

    def loaded(self) -> bool:
        """Return always True as enzyme is always imported."""
        return True

    def accepts(self, video_path: str) -> bool:
        """Accept only MKV files."""
        return video_path.lower().endswith('.mkv')

    @classmethod
    def extract_info(cls, video_path: str) -> typing.Any:
        """Extract info from the video."""
        with open(video_path, 'rb') as f:
            return to_dict(enzyme.MKV(f))

    def describe(
        self, video_path: str, context: typing.MutableMapping[str, typing.Any]
    ) -> typing.MutableMapping[str, typing.Any]:
        """Return video metadata."""
        try:
            data: dict[str, typing.Any] = defaultdict(dict)
            ff = self.extract_info(video_path)

            def debug_data() -> str:
                """Debug data."""
                return json.dumps(ff, cls=get_json_encoder(context), indent=4, ensure_ascii=False)

            context['debug_data'] = debug_data

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    'Video %r scanned using enzyme %r has raw data:\n%s', video_path, enzyme.__version__, debug_data
                )

            data.update(ff)
            if 'info' in data and data['info'] is None:
                return {}
        except enzyme.MalformedMKVError as error:  # pragma: no cover
            raise MalformedFileError from error

        if logger.level == logging.DEBUG:
            logger.debug(
                'Video %r scanned using Enzyme %r has raw data:\n%s',
                video_path,
                enzyme.__version__,
                json.dumps(data, cls=get_json_encoder(context), indent=4, ensure_ascii=False),
            )

        result = self._describe_tracks(
            video_path,
            data.get('info', {}),
            data.get('video_tracks'),
            data.get('audio_tracks'),
            data.get('subtitle_tracks'),
            context,
        )

        if not result:
            raise MalformedFileError

        result['provider'] = {'name': 'enzyme', 'version': self.version}

        return result

    @property
    def version(self) -> typing.Mapping[str, typing.Any]:
        """Return enzyme version information."""
        return {'enzyme': enzyme.__version__}
