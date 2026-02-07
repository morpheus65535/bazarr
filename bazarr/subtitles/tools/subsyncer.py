# coding=utf-8

import logging
import os

from ffsubsync.ffsubsync import run, make_parser

from utilities.binaries import get_binary
from radarr.history import history_log_movie
from sonarr.history import history_log
from subtitles.processing import ProcessSubtitlesResult
from languages.get_languages import language_from_alpha2
from utilities.path_mappings import path_mappings
from app.config import settings
from app.get_args import args


class SubSyncer:
    def __init__(self):
        self.reference = None
        self.srtin = None
        self.srtout = None
        self.ffmpeg_path = None
        self.args = None
        try:
            import webrtcvad  # noqa W0611
        except ImportError:
            self.vad = 'subs_then_auditok'
        else:
            self.vad = 'subs_then_webrtc'
        self.log_dir_path = os.path.join(args.config_dir, 'log')
        self.progress_callback = None
        self.sync_result = None
        self.job_id = None

    def sync(self, video_path, srt_path, srt_lang, hi, forced,
             max_offset_seconds, no_fix_framerate, gss, reference=None, sonarr_series_id=None, sonarr_episode_id=None,
             radarr_id=None, progress_callback=None, job_id=None, force_sync=False):
        self.reference = video_path
        self.srtin = srt_path
        self.progress_callback = progress_callback
        self.sync_result = None

        if self.srtin.casefold().endswith('.ass'):
            # try to preserve the original subtitle style
            # ffmpeg will be able to handle this automatically as long as it has the libass filter
            extension = '.ass'
        else:
            extension = '.srt'
        self.srtout = f'{os.path.splitext(self.srtin)[0]}.synced{extension}'
        self.args = None
        self.job_id = job_id

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
            if reference and reference != video_path and os.path.isfile(reference):
                # subtitles path provided
                self.reference = reference

            unparsed_args = [self.reference, '-i', self.srtin, '-o', self.srtout, '--ffmpegpath', self.ffmpeg_path,
                             '--vad', self.vad, '--log-dir-path', self.log_dir_path, '--max-offset-seconds',
                             max_offset_seconds, '--output-encoding', 'same']

            if no_fix_framerate:
                unparsed_args.append('--no-fix-framerate')

            if gss:
                unparsed_args.append('--gss')

            if reference and isinstance(reference, str) and len(reference) == 3 and reference[:2] in ['a:', 's:']:
                # audio or subtitles track id provided
                unparsed_args.append('--reference-stream')
                unparsed_args.append(reference)
            elif settings.subsync.force_audio and not force_sync:
                # nothing else match and force audio settings is enabled
                unparsed_args.append('--reference-stream')
                unparsed_args.append('a:0')

            if settings.subsync.debug:
                unparsed_args.append('--make-test-case')

            parser = make_parser()
            self.args = parser.parse_args(args=unparsed_args)

            if os.path.isfile(self.srtout):
                os.remove(self.srtout)
                logging.debug('BAZARR deleted the previous subtitles synchronization attempt file.')

            self.sync_result = run(self.args)

            result = self.sync_result
        except Exception:
            logging.exception(
                f'BAZARR an exception occurs during the synchronization process for this subtitle file: {self.srtin}')
        else:
            if settings.subsync.debug:
                return result
            if os.path.isfile(self.srtout):
                if not settings.subsync.debug:
                    os.remove(self.srtin)
                    os.rename(self.srtout, self.srtin)

                    offset_seconds = result['offset_seconds'] or 0
                    framerate_scale_factor = result['framerate_scale_factor'] or 0
                    message = (f"{language_from_alpha2(srt_lang)} subtitles synchronization ended with an offset of "
                               f"{offset_seconds} seconds and a framerate scale factor of "
                               f"{f'{framerate_scale_factor:.2f}'}.")

                    if sonarr_series_id:
                        prr = path_mappings.path_replace_reverse
                    else:
                        prr = path_mappings.path_replace_reverse_movie

                    result = ProcessSubtitlesResult(message=message,
                                                    reversed_path=prr(self.reference),
                                                    downloaded_language_code2=srt_lang,
                                                    downloaded_provider=None,
                                                    score=None,
                                                    forced=forced,
                                                    subtitle_id=None,
                                                    reversed_subtitles_path=prr(self.srtin),
                                                    hearing_impaired=hi)

                    if sonarr_episode_id:
                        history_log(action=5, sonarr_series_id=sonarr_series_id, sonarr_episode_id=sonarr_episode_id,
                                    result=result)
                    else:
                        history_log_movie(action=5, radarr_id=radarr_id, result=result)
            else:
                logging.error(f'BAZARR unable to sync subtitles: {self.srtin}')

            return result
