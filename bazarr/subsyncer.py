import logging
import os
from ffsubsync.ffsubsync import run, make_parser
from utils import get_binary
from utils import history_log, history_log_movie
from get_languages import alpha2_from_alpha3, language_from_alpha3
from helper import path_mappings


class SubSyncer:
    def __init__(self):
        self.reference = None
        self.srtin = None
        self.srtout = None
        self.ffmpeg_path = None
        self.args = None
        self.vad = 'subs_then_auditok'

    def sync(self, video_path, srt_path, srt_lang, media_type, sonarr_series_id=None, sonarr_episode_id=None,
             radarr_id=None):
        self.reference = video_path
        self.srtin = srt_path
        self.srtout = None
        self.args = None

        ffprobe_exe = get_binary('ffprobe')
        if not ffprobe_exe:
            logging.debug('BAZARR FFprobe not found!')
            return
        else:
            logging.debug('BAZARR FFprobe used is %s', ffprobe_exe)

        ffmpeg_exe = get_binary('ffmpeg')
        if not ffmpeg_exe:
            logging.debug('BAZARR FFmpeg not found!')
            return
        else:
            logging.debug('BAZARR FFmpeg used is %s', ffmpeg_exe)

        self.ffmpeg_path = os.path.dirname(ffmpeg_exe)
        try:
            unparsed_args = [self.reference, '-i', self.srtin, '--overwrite-input', '--ffmpegpath', self.ffmpeg_path,
                             '--vad', self.vad]
            parser = make_parser()
            self.args = parser.parse_args(args=unparsed_args)
            result = run(self.args)
        except Exception as e:
            logging.exception('BAZARR an exception occurs during the synchronization process for this subtitles: '
                              '{0}'.format(self.srtin))
        else:
            if result['sync_was_successful']:
                message = "{0} subtitles synchronization ended with an offset of {1} seconds and a framerate scale " \
                          "factor of {2}.".format(language_from_alpha3(srt_lang), result['offset_seconds'],
                                                  "{:.2f}".format(result['framerate_scale_factor']))

                if media_type == 'series':
                    history_log(action=5, sonarr_series_id=sonarr_series_id, sonarr_episode_id=sonarr_episode_id,
                                description=message, video_path=path_mappings.path_replace_reverse(self.reference),
                                language=alpha2_from_alpha3(srt_lang), subtitles_path=srt_path)
                else:
                    history_log_movie(action=5, radarr_id=radarr_id, description=message,
                                      video_path=path_mappings.path_replace_reverse_movie(self.reference),
                                      language=alpha2_from_alpha3(srt_lang), subtitles_path=srt_path)
            else:
                logging.error('BAZARR unable to sync subtitles: {0}'.format(self.srtin))

            return result


subsync = SubSyncer()
