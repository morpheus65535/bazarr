# coding=utf-8

import enzyme
from enzyme.exceptions import MalformedMKVError
import logging
import os
from knowit import api


class EmbeddedSubsReader:
    def __init__(self):
        self.ffprobe = None
    
    def list_languages(self, file):
        from utils import get_binary
        self.ffprobe = get_binary("ffprobe")

        subtitles_list = []
        if self.ffprobe:
            api.initialize({'provider': 'ffmpeg', 'ffmpeg': self.ffprobe})
            data = api.know(file)

            traditional_chinese = ["cht", "tc", "traditional", "zht", "hant", "big5", u"繁", u"雙語"]
            brazilian_portuguese = ["pt-br", "pob", "pb", "brazilian", "brasil", "brazil"]

            if 'subtitle' in data:
                for detected_language in data['subtitle']:
                    if 'language' in detected_language:
                        language = detected_language['language'].alpha3
                        if language == 'zho' and 'name' in detected_language:
                            if any (ext in (detected_language['name'].lower()) for ext in traditional_chinese):
                                language = 'zht'
                        if language == 'por' and 'name' in detected_language:
                            if any (ext in (detected_language['name'].lower()) for ext in brazilian_portuguese):
                                language = 'pob'
                        forced = detected_language['forced'] if 'forced' in detected_language else False
                        hearing_impaired = detected_language['hearing_impaired'] if 'hearing_impaired' in \
                                                                                    detected_language else False
                        codec = detected_language['format'] if 'format' in detected_language else None
                        subtitles_list.append([language, forced, hearing_impaired, codec])
                    else:
                        continue
        else:
            if os.path.splitext(file)[1] == '.mkv':
                with open(file, 'rb') as f:
                    try:
                        mkv = enzyme.MKV(f)
                    except MalformedMKVError:
                        logging.error('BAZARR cannot analyze this MKV with our built-in MKV parser, you should install ffmpeg: ' + file)
                    else:
                        for subtitle_track in mkv.subtitle_tracks:
                            hearing_impaired = False
                            if subtitle_track.name:
                                if 'sdh' in subtitle_track.name.lower():
                                    hearing_impaired = True
                            subtitles_list.append([subtitle_track.language, subtitle_track.forced, hearing_impaired,
                                                   subtitle_track.codec_id])

        return subtitles_list


embedded_subs_reader = EmbeddedSubsReader()
