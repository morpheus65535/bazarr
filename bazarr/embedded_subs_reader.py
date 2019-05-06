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
        if self.ffprobe:
            try:
                if not settings.general.getboolean('ignore_pgs_subs'):
                    return subprocess.check_output([self.ffprobe, "-loglevel", "error", "-select_streams", "s", "-show_entries", "stream_tags=language", "-of", "csv=p=0", file.encode(locale.getpreferredencoding())], universal_newlines=True, stderr=subprocess.STDOUT).strip().split("\n")
                subtitle_tracks = subprocess.check_output([self.ffprobe, "-loglevel", "error", "-select_streams", "s", "-show_entries", "stream=codec_name:stream_tags=language", "-of", "csv=p=0", file.encode(locale.getpreferredencoding())], universal_newlines=True, stderr=subprocess.STDOUT).strip().split("\n")
                return [lang for (sub_type, lang) in map(lambda subtitle_track: subtitle_track.split(','), subtitle_tracks) if sub_type != 'hdmv_pgs_subtitle']
            except subprocess.CalledProcessError as e:
                raise FFprobeError(e.output)
        if os.path.splitext(file)[1] != '.mkv':
            raise NotMKVAndNoFFprobe()
        with open(file, 'rb') as f:
            mkv = enzyme.MKV(f)
        if not settings.general.getboolean('ignore_pgs_subs'):
            return [subtitle_track.language for subtitle_track in mkv.subtitle_tracks]
        return [subtitle_track.language for subtitle_track in mkv.subtitle_tracks if subtitle_track.codec_id != "S_HDMV/PGS"]

embedded_subs_reader = EmbeddedSubsReader()