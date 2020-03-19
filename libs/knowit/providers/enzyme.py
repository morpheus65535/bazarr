# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import logging
from collections import defaultdict
from logging import NullHandler, getLogger
import enzyme

from .. import OrderedDict
from ..properties import (
    AudioCodec,
    Basic,
    Duration,
    Language,
    Quantity,
    VideoCodec,
    YesNo,
)
from ..property import Property
from ..provider import (
    MalformedFileError,
    Provider,
)
from ..rules import (
    AudioChannelsRule,
    ClosedCaptionRule,
    HearingImpairedRule,
    LanguageRule,
    ResolutionRule,
)
from ..serializer import get_json_encoder
from ..units import units
from ..utils import todict

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class EnzymeProvider(Provider):
    """Enzyme Provider."""

    def __init__(self, config, *args, **kwargs):
        """Init method."""
        super(EnzymeProvider, self).__init__(config, {
            'general': OrderedDict([
                ('title', Property('title', description='media title')),
                ('duration', Duration('duration', description='media duration')),
            ]),
            'video': OrderedDict([
                ('id', Basic('number', int, description='video track number')),
                ('name', Property('name', description='video track name')),
                ('language', Language('language', description='video language')),
                ('width', Quantity('width', units.pixel)),
                ('height', Quantity('height', units.pixel)),
                ('scan_type', YesNo('interlaced', yes='Interlaced', no='Progressive', default='Progressive',
                                    description='video scan type')),
                ('resolution', None),  # populated with ResolutionRule
                # ('bit_depth', Property('bit_depth', Integer('video bit depth'))),
                ('codec', VideoCodec(config, 'codec_id', description='video codec')),
                ('forced', YesNo('forced', hide_value=False, description='video track forced')),
                ('default', YesNo('default', hide_value=False, description='video track default')),
                ('enabled', YesNo('enabled', hide_value=True, description='video track enabled')),
            ]),
            'audio': OrderedDict([
                ('id', Basic('number', int, description='audio track number')),
                ('name', Property('name', description='audio track name')),
                ('language', Language('language', description='audio language')),
                ('codec', AudioCodec(config, 'codec_id', description='audio codec')),
                ('channels_count', Basic('channels', int, description='audio channels count')),
                ('channels', None),  # populated with AudioChannelsRule
                ('forced', YesNo('forced', hide_value=False, description='audio track forced')),
                ('default', YesNo('default', hide_value=False, description='audio track default')),
                ('enabled', YesNo('enabled', hide_value=True, description='audio track enabled')),
            ]),
            'subtitle': OrderedDict([
                ('id', Basic('number', int, description='subtitle track number')),
                ('name', Property('name', description='subtitle track name')),
                ('language', Language('language', description='subtitle language')),
                ('hearing_impaired', None),  # populated with HearingImpairedRule
                ('closed_caption', None),  # populated with ClosedCaptionRule
                ('forced', YesNo('forced', hide_value=False, description='subtitle track forced')),
                ('default', YesNo('default', hide_value=False, description='subtitle track default')),
                ('enabled', YesNo('enabled', hide_value=True, description='subtitle track enabled')),
            ]),
        }, {
            'video': OrderedDict([
                ('language', LanguageRule('video language')),
                ('resolution', ResolutionRule('video resolution')),
            ]),
            'audio': OrderedDict([
                ('language', LanguageRule('audio language')),
                ('channels', AudioChannelsRule('audio channels')),
            ]),
            'subtitle': OrderedDict([
                ('language', LanguageRule('subtitle language')),
                ('hearing_impaired', HearingImpairedRule('subtitle hearing impaired')),
                ('closed_caption', ClosedCaptionRule('closed caption')),
            ])
        })

    def accepts(self, video_path):
        """Accept only MKV files."""
        return video_path.lower().endswith('.mkv')

    @classmethod
    def extract_info(cls, video_path):
        """Extract info from the video."""
        with open(video_path, 'rb') as f:
            return todict(enzyme.MKV(f))

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
                         video_path=video_path, version=enzyme.__version__, data=json.dumps(data))

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
