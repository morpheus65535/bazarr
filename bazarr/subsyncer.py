import logging
import os
from ffsubsync.ffsubsync import run
from ffsubsync.constants import *
from knowit import api
from utils import get_binary


class SubSyncer:
    def __init__(self):
        self.reference = None
        self.srtin = None
        self.reference_stream = None
        self.overwrite_input = True
        self.ffmpeg_path = None

        # unused attributes
        self.encoding = DEFAULT_ENCODING
        self.vlc_mode = None
        self.make_test_case = None
        self.gui_mode = None
        self.srtout = None
        self.vad = 'subs_then_auditok'
        self.reference_encoding = None
        self.frame_rate = DEFAULT_FRAME_RATE
        self.start_seconds = DEFAULT_START_SECONDS
        self.no_fix_framerate = None
        self.serialize_speech = None
        self.max_offset_seconds = DEFAULT_MAX_OFFSET_SECONDS
        self.merge_with_reference = None
        self.output_encoding = 'same'

    def sync(self, video_path, srt_path, srt_lang):
        self.reference = video_path
        self.srtin = srt_path
        self.srtout = None

        ffprobe_exe = get_binary('ffprobe')
        if not ffprobe_exe:
            logging.debug('BAZARR FFprobe not found!')
            return
        else:
            logging.debug('BAZARR FFprobe used is %s', ffprobe_exe)

        api.initialize({'provider': 'ffmpeg', 'ffmpeg': ffprobe_exe})
        data = api.know(self.reference)

        if 'subtitle' in data:
            for i, embedded_subs in enumerate(data['subtitle']):
                if 'language' in embedded_subs:
                    language = embedded_subs['language'].alpha3
                    if language == "eng":
                        self.reference_stream = "s:{}".format(i)
                        break
            if not self.reference_stream:
                self.reference_stream = "s:0"
        elif 'audio' in data:
            audio_tracks = data['audio']
            for i, audio_track in enumerate(audio_tracks):
                if 'language' in audio_track:
                    language = audio_track['language'].alpha3
                    if language == srt_lang:
                        self.reference_stream = "a:{}".format(i)
                        break
            if not self.reference_stream:
                audio_tracks = data['audio']
                for i, audio_track in enumerate(audio_tracks):
                    if 'language' in audio_track:
                        language = audio_track['language'].alpha3
                        if language == "eng":
                            self.reference_stream = "a:{}".format(i)
                            break
                if not self.reference_stream:
                    self.reference_stream = "a:0"
        else:
            raise NoAudioTrack

        ffmpeg_exe = get_binary('ffmpeg')
        if not ffmpeg_exe:
            logging.debug('BAZARR FFmpeg not found!')
            return
        else:
            logging.debug('BAZARR FFmpeg used is %s', ffmpeg_exe)

        self.ffmpeg_path = os.path.dirname(ffmpeg_exe)
        run(self)

class NoAudioTrack(Exception):
    """Exception raised if no audio track can be found in video file."""
    pass


subsync = SubSyncer()
