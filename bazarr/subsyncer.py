import logging
import os
from ffsubsync.ffsubsync import run
from ffsubsync.constants import *
from knowit import api
from utils import get_binary
from utils import history_log, history_log_movie
from get_languages import alpha2_from_alpha3, language_from_alpha3
from helper import path_mappings


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

    def sync(self, video_path, srt_path, srt_lang, media_type, sonarr_series_id=None, sonarr_episode_id=None,
             radarr_id=None):
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

        using_what = None

        if 'subtitle' in data:
            for i, embedded_subs in enumerate(data['subtitle']):
                if 'language' in embedded_subs:
                    language = embedded_subs['language'].alpha3
                    if language == "eng":
                        using_what = "English embedded subtitle track"
                        self.reference_stream = "s:{}".format(i)
                        break
            if not self.reference_stream:
                using_what = "{0} embedded subtitle track".format(
                    language_from_alpha3(embedded_subs['language'].alpha3) or 'unknown language embedded subtitles '
                                                                              'track')
                self.reference_stream = "s:0"
        elif 'audio' in data:
            audio_tracks = data['audio']
            for i, audio_track in enumerate(audio_tracks):
                if 'language' in audio_track:
                    language = audio_track['language'].alpha3
                    if language == srt_lang:
                        using_what = "{0} audio track".format(language_from_alpha3(audio_track['language'].alpha3) or
                                                              'unknown language audio track')
                        self.reference_stream = "a:{}".format(i)
                        break
            if not self.reference_stream:
                audio_tracks = data['audio']
                for i, audio_track in enumerate(audio_tracks):
                    if 'language' in audio_track:
                        language = audio_track['language'].alpha3
                        if language == "eng":
                            using_what = "English audio track"
                            self.reference_stream = "a:{}".format(i)
                            break
                if not self.reference_stream:
                    using_what = "first audio track"
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
        try:
            result = run(self)
        except Exception as e:
            logging.error('BAZARR an exception occurs during the synchronization process for this subtitles: ' +
                          self.srtin)
        else:
            if result['sync_was_successful']:
                message = "{0} subtitles synchronization ended with an offset of {1} seconds and a framerate scale " \
                          "factor of {2} using {3} (0:{4}).".format(language_from_alpha3(srt_lang),
                                                                    result['offset_seconds'],
                                                                    result['framerate_scale_factor'],
                                                                    using_what,
                                                                    self.reference_stream)

                if media_type == 'series':
                    history_log(action=5, sonarr_series_id=sonarr_series_id, sonarr_episode_id=sonarr_episode_id,
                                description=message, video_path=path_mappings.path_replace_reverse(self.reference),
                                language=alpha2_from_alpha3(srt_lang), subtitles_path=srt_path)
                else:
                    history_log_movie(action=5, radarr_id=radarr_id, description=message,
                                      video_path=path_mappings.path_replace_reverse_movie(self.reference),
                                      language=alpha2_from_alpha3(srt_lang), subtitles_path=srt_path)
            else:
                logging.error('BAZARR unable to sync subtitles using {0}({1}): {2}'.format(using_what,
                                                                                           self.reference_stream,
                                                                                           self.srtin))

            return result


class NoAudioTrack(Exception):
    """Exception raised if no audio track can be found in video file."""
    pass


subsync = SubSyncer()
