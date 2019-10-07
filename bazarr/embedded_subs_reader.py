import enzyme
import logging
import os
import subprocess
import locale

from utils import get_binary
from pyprobe.pyprobe import VideoFileParser

class NotMKVAndNoFFprobe(Exception):
    pass

class FFprobeError(Exception):
    pass

class EmbeddedSubsReader:
    def __init__(self):
        self.ffprobe = get_binary("ffprobe")
    
    def list_languages(self, file):
        subtitles_list = []

        if self.ffprobe:
            parser = VideoFileParser(ffprobe=self.ffprobe, includeMissing=True, rawMode=False)
            data = parser.parseFfprobe(file)

            for detected_language in data['subtitles']:
                subtitles_list.append([detected_language['language'], detected_language['forced'], detected_language["codec"]])
        else:
            if os.path.splitext(file)[1] == '.mkv':
                with open(file, 'rb') as f:
                    mkv = enzyme.MKV(f)
                for subtitle_track in mkv.subtitle_tracks:
                    subtitles_list.append([subtitle_track.language, subtitle_track.forced, subtitle_track.codec_id])

        return subtitles_list


embedded_subs_reader = EmbeddedSubsReader()
