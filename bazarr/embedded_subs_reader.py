import enzyme
from enzyme.exceptions import MalformedMKVError
import logging
import os
from knowit import api

from utils import get_binary


class EmbeddedSubsReader:
    def __init__(self):
        self.ffprobe = get_binary("ffprobe")
    
    def list_languages(self, file):
        subtitles_list = []

        if self.ffprobe:
            api.initialize({'provider': 'ffmpeg', 'ffmpeg': self.ffprobe})
            data = api.know(file)

            if 'subtitle' in data:
                for detected_language in data['subtitle']:
                    if 'language' in detected_language:
                        language = detected_language['language'].alpha3
                        forced = detected_language['forced'] if 'forced' in detected_language else None
                        codec = detected_language['format'] if 'format' in detected_language else None
                        subtitles_list.append([language, forced, codec])
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
                            subtitles_list.append([subtitle_track.language, subtitle_track.forced, subtitle_track.codec_id])

        return subtitles_list


embedded_subs_reader = EmbeddedSubsReader()
