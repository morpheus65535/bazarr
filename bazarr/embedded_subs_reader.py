import enzyme
import logging

from subprocess import check_output
from utils import get_binary

class EmbeddedSubsReader:
    def __init__(self):
        self.ffprobe = get_binary("ffprobe")
    
    def list_languages(self, file):
        if self.ffprobe:
            return check_output([self.ffprobe, "-loglevel", "quiet", "-select_streams", "s", "-show_entries", "stream_tags=language", "-of", "csv=p=0", file], universal_newlines=True).strip().split("\n")
        else:
            with open(file, 'rb') as f:
                mkv = enzyme.MKV(f)
            return [subtitle_track.language for subtitle_track in mkv.subtitle_tracks]

embedded_subs_reader = EmbeddedSubsReader()