# pylama:ignore=W0611
# TODO unignore and fix W0611

import logging
import os
from ffsubsync.ffsubsync import run, make_parser
from utils import get_binary
from utils import history_log, history_log_movie
from get_languages import language_from_alpha2
from config import settings
from get_args import args


class SubSyncer:
    def __init__(self):
        self.reference = None
        self.srtin = None
        self.srtout = None
        self.ffmpeg_path = None
        self.args = None
        try:
            import webrtcvad
        except ImportError:
            self.vad = 'subs_then_auditok'
        else:
            self.vad = 'subs_then_webrtc'
        self.log_dir_path = os.path.join(args.config_dir, 'log')

    def sync(self, video_path, srt_path, srt_lang, media_type, series_id=None, episode_id=None,
             movie_id=None):
        self.reference = video_path
        self.srtin = srt_path
        self.srtout = '{}.synced.srt'.format(os.path.splitext(self.srtin)[0])
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
            unparsed_args = [self.reference, '-i', self.srtin, '-o', self.srtout, '--ffmpegpath', self.ffmpeg_path,
                             '--vad', self.vad, '--log-dir-path', self.log_dir_path]
            if settings.subsync.getboolean('debug'):
                unparsed_args.append('--make-test-case')
            parser = make_parser()
            self.args = parser.parse_args(args=unparsed_args)
            result = run(self.args)
        except Exception:
            logging.exception('BAZARR an exception occurs during the synchronization process for this subtitles: '
                              '{0}'.format(self.srtin))
        else:
            if settings.subsync.getboolean('debug'):
                return result
            if os.path.isfile(self.srtout):
                if not settings.subsync.getboolean('debug'):
                    os.remove(self.srtin)
                    os.rename(self.srtout, self.srtin)

                    offset_seconds = result['offset_seconds'] or 0
                    framerate_scale_factor = result['framerate_scale_factor'] or 0
                    message = "{0} subtitles synchronization ended with an offset of {1} seconds and a framerate " \
                              "scale factor of {2}.".format(language_from_alpha2(srt_lang), offset_seconds,
                                                            "{:.2f}".format(framerate_scale_factor))

                    if media_type == 'series':
                        history_log(action=5, series_id=series_id, episode_id=episode_id,
                                    description=message, video_path=self.reference, language=srt_lang,
                                    subtitles_path=srt_path)
                    else:
                        history_log_movie(action=5, movie_id=movie_id, description=message,
                                          video_path=self.reference, language=srt_lang, subtitles_path=srt_path)
            else:
                logging.error('BAZARR unable to sync subtitles: {0}'.format(self.srtin))

            return result


subsync = SubSyncer()
