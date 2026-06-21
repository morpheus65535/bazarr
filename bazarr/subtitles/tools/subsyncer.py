# coding=utf-8

import logging
import os

from ffsubsync.ffsubsync import run, make_parser
from ffsubsync import ProgressInfo

from utilities.binaries import get_binary
from radarr.history import history_log_movie
from sonarr.history import history_log
from subtitles.processing import ProcessSubtitlesResult
from languages.get_languages import audio_language_from_name, language_from_alpha2
from utilities.path_mappings import path_mappings
from utilities.video_analyzer import subtitles_sync_references
from app.config import settings
from app.database import TableMovies, TableShows, database, select
from app.get_args import args
from app.jobs_queue import jobs_queue


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
        self.sync_result = None
        self.job_id = None

    @staticmethod
    def _original_language_name(sonarr_series_id, radarr_id):
        """Read originalLanguage from the local DB. The column is populated by the regular
        Sonarr/Radarr series/movies sync. Returns None if the row is missing or the column
        hasn't been backfilled yet (next series/movies sync will populate it)."""
        try:
            if sonarr_series_id:
                row = database.execute(
                    select(TableShows.originalLanguage)
                    .where(TableShows.sonarrSeriesId == int(sonarr_series_id))
                ).first()
                return row.originalLanguage if row else None
            if radarr_id:
                row = database.execute(
                    select(TableMovies.originalLanguage)
                    .where(TableMovies.radarrId == int(radarr_id))
                ).first()
                return row.originalLanguage if row else None
        except Exception:
            logging.exception('BAZARR could not retrieve originalLanguage from database.')
        return None

    @classmethod
    def _audio_stream_for_original_language(cls, sonarr_series_id=None, sonarr_episode_id=None, radarr_id=None):
        """Return the ffmpeg audio stream specifier (e.g. 'a:1') matching the show/movie's
        original language as reported by Sonarr/Radarr, or None if not found."""
        logging.debug(f"BAZARR subsync: looking up original language "
                     f"(sonarr_series_id={sonarr_series_id}, sonarr_episode_id={sonarr_episode_id}, "
                     f"radarr_id={radarr_id})")
        target_name = cls._original_language_name(sonarr_series_id=sonarr_series_id, radarr_id=radarr_id)
        logging.debug(f"BAZARR subsync: original language reported by Sonarr/Radarr = {target_name!r}")
        if not target_name:
            return None
        try:
            refs = subtitles_sync_references(subtitles_path='',
                                             sonarr_episode_id=sonarr_episode_id,
                                             radarr_movie_id=radarr_id)
        except Exception:
            logging.exception('BAZARR could not enumerate audio tracks for original-language matching.')
            return None
        audio_tracks = refs.get('audio_tracks', []) if isinstance(refs, dict) else []
        logging.debug(f"BAZARR subsync: file audio tracks = "
                     f"{[(t.get('stream'), t.get('language')) for t in audio_tracks]}")
        # Direct name match (covers most cases)
        for track in audio_tracks:
            if track.get('language') == target_name:
                logging.debug(f"BAZARR subsync: matched original language {target_name!r} to audio track "
                             f"{track.get('stream')}")
                return track.get('stream')
        # Bazarr renames a couple of languages internally (Chinese -> Chinese Simplified, Modern Greek -> Greek);
        # try the normalized form as a fallback.
        normalized = audio_language_from_name(target_name)
        if normalized and normalized != target_name:
            for track in audio_tracks:
                if track.get('language') == normalized:
                    logging.debug(f"BAZARR subsync: matched normalized original language {normalized!r} "
                                 f"(from {target_name!r}) to audio track {track.get('stream')}")
                    return track.get('stream')
        logging.debug(f"BAZARR subsync: original language {target_name!r} not found in audio tracks; "
                     f"falling back")
        return None

    def _on_progress(self, info: ProgressInfo) -> None:
        # info.processed_seconds / info.total_seconds (total may be None);
        # info.fraction is a 0.0-1.0 ratio (None if the total is unknown).
        if info.total_seconds is not None:
            jobs_queue.update_job_progress(job_id=self.job_id,
                                           progress_value=info.processed_seconds,
                                           progress_max=info.total_seconds)

    def sync(self, video_path, srt_path, srt_lang, hi, forced,
             max_offset_seconds, no_fix_framerate, gss, reference=None, sonarr_series_id=None, sonarr_episode_id=None,
             radarr_id=None, job_id=None, force_sync=False):
        self.reference = video_path
        self.srtin = srt_path
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

            logging.debug(f"BAZARR subsync: settings — force_audio={settings.subsync.force_audio} "
                         f"use_original_language={settings.subsync.use_original_language} "
                         f"auto_use_original_language={settings.subsync.auto_use_original_language} "
                         f"force_sync={force_sync}")
            if reference and isinstance(reference, str) and len(reference) == 3 and reference[:2] in ['a:', 's:']:
                # audio or subtitles track id provided
                unparsed_args.append('--reference-stream')
                unparsed_args.append(reference)
            elif settings.subsync.force_audio and not force_sync:
                # auto-sync with force_audio: use a:0, optionally overridden by original-language match
                stream_spec = 'a:0'
                if settings.subsync.use_original_language:
                    matched = self._audio_stream_for_original_language(
                        sonarr_series_id=sonarr_series_id,
                        sonarr_episode_id=sonarr_episode_id,
                        radarr_id=radarr_id,
                    )
                    if matched:
                        stream_spec = matched
                logging.debug(f"BAZARR subsync: using --reference-stream {stream_spec}")
                unparsed_args.append('--reference-stream')
                unparsed_args.append(stream_spec)
            elif settings.subsync.use_original_language or settings.subsync.auto_use_original_language:
                # original-language preference active. Applies to both manual and
                # automatic sync; does NOT change Bazarr's existing force_audio
                # behavior (which only fires during auto-sync).
                matched = self._audio_stream_for_original_language(
                    sonarr_series_id=sonarr_series_id,
                    sonarr_episode_id=sonarr_episode_id,
                    radarr_id=radarr_id,
                )
                if matched:
                    logging.debug(f"BAZARR subsync: using --reference-stream {matched}")
                    unparsed_args.append('--reference-stream')
                    unparsed_args.append(matched)
                else:
                    logging.debug("BAZARR subsync: no original-language match; using ffsubsync default reference")

            if settings.subsync.debug:
                unparsed_args.append('--make-test-case')

            parser = make_parser()
            self.args = parser.parse_args(args=unparsed_args)

            if os.path.isfile(self.srtout):
                os.remove(self.srtout)
                logging.debug('BAZARR deleted the previous subtitles synchronization attempt file.')

            self.sync_result = run(self.args, progress_handler=self._on_progress)

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
