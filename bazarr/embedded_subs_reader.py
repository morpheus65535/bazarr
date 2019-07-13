import enzyme
import logging
import os
import subprocess
import locale

from config import settings
from utils import get_binary

class NotMKVAndNoFFprobe(Exception):
    pass

class FFprobeError(Exception):
    pass

class EmbeddedSubsReader:
    def __init__(self):
        self.ffprobe = get_binary("ffprobe")
    
    def list_languages(self, file):
        subtitles_list = []

        if os.path.splitext(file)[1] == '.mkv':
            with open(file, 'rb') as f:
                mkv = enzyme.MKV(f)
            for subtitle_track in mkv.subtitle_tracks:
                subtitles_list.append([subtitle_track.language, subtitle_track.forced])
        else:
            if self.ffprobe:
                detected_languages = []
                try:
                    detected_languages = subprocess.check_output([self.ffprobe, "-loglevel", "error", "-select_streams", "s", "-show_entries", "stream_tags=language", "-of", "csv=p=0", file.encode(locale.getpreferredencoding())], universal_newlines=True, stderr=subprocess.STDOUT).strip().split("\n")
                except subprocess.CalledProcessError as e:
                    raise FFprobeError(e.output)
                else:
                    for detected_language in detected_languages:
                        subtitles_list.append([detected_language, False])
                        # I can't get the forced flag from ffprobe so I always assume it isn't forced

        return subtitles_list


embedded_subs_reader = EmbeddedSubsReader()