import enzyme
import logging
import os
import subprocess

from utils import get_binary

class MKVAndNoFFprobe(Exception):
    pass

class FFprobeError(Exception):
    pass

class EmbeddedSubsReader:
    def __init__(self):
        self.ffprobe = get_binary("ffprobe")
    
    def list_languages(self, file):
        if self.ffprobe:
            try:
                return subprocess.check_output([self.ffprobe, "-loglevel", "error", "-select_streams", "s", "-show_entries", "stream_tags=language", "-of", "csv=p=0", file], universal_newlines=True, stderr=subprocess.STDOUT).strip().split("\n")
            except subprocess.CalledProcessError as e:
                raise FFprobeError(e.output)
        if os.path.splitext(file)[1] != '.mkv':
            raise MKVAndNoFFprobe()
        with open(file, 'rb') as f:
            mkv = enzyme.MKV(f)
        return [subtitle_track.language for subtitle_track in mkv.subtitle_tracks]

embedded_subs_reader = EmbeddedSubsReader()