# coding=utf-8
# fmt: off

import logging

from app.config import settings, sync_checker as _defaul_sync_checker
from utilities.path_mappings import path_mappings
from utilities.post_processing import pp_replace, set_chmod
from utilities.autopulse_webhook import call_external_webhook
from languages.get_languages import alpha2_from_alpha3, alpha2_from_language, alpha3_from_language, language_from_alpha3
from app.database import TableShows, TableEpisodes, TableMovies, database, select
from utilities.analytics import event_tracker
from radarr.notify import notify_radarr
from sonarr.notify import notify_sonarr
from plex.operations import plex_set_movie_added_date_now, plex_update_library, plex_set_episode_added_date_now, plex_refresh_item
from jellyfin.operations import jellyfin_refresh_item
from app.event_handler import event_stream

from .utils import _get_download_code3
from .post_processing import postprocessing
from .utils import _get_scores


class ProcessSubtitlesResult:
    def __init__(self, message, reversed_path, downloaded_language_code2, downloaded_provider, score, forced,
                 subtitle_id, reversed_subtitles_path, hearing_impaired, matched=None, not_matched=None):
        self.message = message
        self.path = reversed_path
        self.provider = downloaded_provider
        self.score = score
        self.subs_id = subtitle_id
        self.subs_path = reversed_subtitles_path
        self.matched = matched
        self.not_matched = not_matched

        if hearing_impaired:
            self.language_code = f"{downloaded_language_code2}:hi"
        elif forced:
            self.language_code = f"{downloaded_language_code2}:forced"
        else:
            self.language_code = downloaded_language_code2


def _trigger_auto_translation(downloaded_lang, subtitle_path, video_path, media_type,
                              series_id=None, episode_id=None, radarr_id=None,
                              source_score_percent=None):
    """
    After a subtitle is downloaded, check if any profile language is configured to
    auto-translate from the just-downloaded language. If so, queue translation.
    Providers are still searched first (translation fires as a parallel fallback).

    source_score_percent: 0-100 score of the just-downloaded source subtitle. If
    provided and below settings.translator.min_source_score, translation is
    skipped (poorly-matched sources shouldn't seed translations).
    """
    try:
        from app.database import get_profile_id, get_profiles_list
        from subtitles.tools.translate.main import translate_subtitles_file
        from subtitles.download import check_missing_languages

        if not subtitle_path or not downloaded_lang:
            return

        # Forced subtitles: don't auto-translate from forced sources
        if subtitle_path and ':forced' in str(downloaded_lang):
            return

        # Quality gate: only translate from sufficiently good source subtitles.
        min_score = settings.translator.min_source_score
        if source_score_percent is not None and source_score_percent < min_score:
            logging.info(
                f'BAZARR auto-translate skipped: source score {source_score_percent:.1f}% '
                f'below threshold {min_score}% for {video_path}'
            )
            return

        # Get the profile for this media item
        if media_type == 'series' and episode_id:
            profile_id = get_profile_id(episode_id=episode_id)
        elif media_type == 'series' and series_id:
            profile_id = get_profile_id(series_id=series_id)
        else:
            profile_id = get_profile_id(movie_id=radarr_id)

        if not profile_id:
            return

        profile = get_profiles_list(profile_id=profile_id)
        if not profile:
            return

        for item in profile.get('items', []):
            target_lang = item.get('language')
            translate_from = item.get('translate_from')

            # Only trigger if this item has translate_from set to the downloaded language
            if not translate_from or translate_from != downloaded_lang:
                continue
            # Don't translate a language to itself
            if target_lang == downloaded_lang:
                continue

            # Check if target language subtitle is still needed.
            # check_missing_languages returns a set of subzero Language objects
            # (alpha3 with .hi/.forced flags). Convert to alpha2 codes for comparison.
            missing = check_missing_languages(path=video_path, media_type=media_type)
            missing_codes = set()
            for lang_obj in missing or []:
                try:
                    code2 = alpha2_from_alpha3(lang_obj.alpha3)
                except Exception:
                    code2 = None
                if not code2:
                    continue
                if getattr(lang_obj, 'hi', False):
                    missing_codes.add(f'{code2}:hi')
                elif getattr(lang_obj, 'forced', False):
                    missing_codes.add(f'{code2}:forced')
                else:
                    missing_codes.add(code2)

            target_codes = {target_lang, f'{target_lang}:hi', f'{target_lang}:forced'}
            if not (missing_codes & target_codes):
                logging.debug(f'BAZARR auto-translate skipped: {target_lang} already satisfied for {video_path}')
                continue

            logging.info(f'BAZARR auto-translate queuing {downloaded_lang} -> {target_lang} for {video_path}')
            # Normalize media_type to match translate_subtitles_file convention
            translate_media_type = 'series' if media_type == 'series' else 'movies'
            translate_subtitles_file(
                video_path=video_path,
                source_srt_file=subtitle_path,
                from_lang=downloaded_lang,
                to_lang=target_lang,
                forced=item.get('forced') == 'True',
                hi=item.get('hi') == 'True',
                media_type=translate_media_type,
                sonarr_series_id=series_id,
                sonarr_episode_id=episode_id,
                radarr_id=radarr_id,
                metadata=None,
            )
    except Exception:
        logging.exception('BAZARR error in _trigger_auto_translation')


def process_subtitle(subtitle, media_type, audio_language, path, max_score, is_upgrade=False, is_manual=False,
                     job_id=None):
    use_postprocessing = settings.general.use_postprocessing
    postprocessing_cmd = settings.general.postprocessing_cmd

    downloaded_provider = subtitle.provider_name
    uploader = subtitle.uploader
    release_info = subtitle.release_info
    downloaded_language_code3 = _get_download_code3(subtitle)

    downloaded_language = language_from_alpha3(downloaded_language_code3)
    downloaded_language_code2 = alpha2_from_alpha3(downloaded_language_code3)
    audio_language_code2 = alpha2_from_language(audio_language)
    audio_language_code3 = alpha3_from_language(audio_language)
    downloaded_path = subtitle.storage_path
    subtitle_id = subtitle.id
    if subtitle.language.hi:
        modifier_string = " HI"
    elif subtitle.language.forced:
        modifier_string = " forced"
    else:
        modifier_string = ""
    logging.debug(f'BAZARR Subtitles file saved to disk: {downloaded_path}')
    if is_upgrade:
        action = "upgraded"
    elif is_manual:
        action = "manually downloaded"
    else:
        action = "downloaded"

    percent_score = round(subtitle.score * 100 / max_score, 2)
    message = (f"{downloaded_language}{modifier_string} subtitles {action} from {downloaded_provider} with a score of "
               f"{percent_score}%.")

    sync_checker = _defaul_sync_checker
    logging.debug("Sync checker: %s", sync_checker)

    if media_type == 'series':
        episode_metadata = database.execute(
            select(TableShows.imdbId, TableShows.tvdbId, TableEpisodes.sonarrSeriesId,
                   TableEpisodes.sonarrEpisodeId, TableEpisodes.season, TableEpisodes.episode)
                .join(TableShows)\
                .where(TableEpisodes.path == path_mappings.path_replace_reverse(path)))\
            .first()
        if not episode_metadata:
            return
        series_id = episode_metadata.sonarrSeriesId
        episode_id = episode_metadata.sonarrEpisodeId

        if sync_checker(subtitle) is True:
            from .sync import sync_subtitles
            sync_subtitles(video_path=path, srt_path=downloaded_path,
                           forced=subtitle.language.forced,
                           hi=subtitle.language.hi,
                           srt_lang=downloaded_language_code2,
                           percent_score=percent_score,
                           sonarr_series_id=episode_metadata.sonarrSeriesId,
                           sonarr_episode_id=episode_metadata.sonarrEpisodeId,
                           job_id=job_id)
    else:
        movie_metadata = database.execute(
            select(TableMovies.radarrId, TableMovies.imdbId, TableMovies.tmdbId)
                .where(TableMovies.path == path_mappings.path_replace_reverse_movie(path)))\
            .first()
        if not movie_metadata:
            return
        series_id = ""
        episode_id = movie_metadata.radarrId

        if sync_checker(subtitle) is True:
            from .sync import sync_subtitles
            sync_subtitles(video_path=path, srt_path=downloaded_path,
                           forced=subtitle.language.forced,
                           hi=subtitle.language.hi,
                           srt_lang=downloaded_language_code2,
                           percent_score=percent_score,
                           radarr_id=movie_metadata.radarrId,
                           job_id=job_id)

    if use_postprocessing is True:
        command = pp_replace(postprocessing_cmd, path, downloaded_path, downloaded_language, downloaded_language_code2,
                             downloaded_language_code3, audio_language, audio_language_code2, audio_language_code3,
                             percent_score, subtitle_id, downloaded_provider, uploader, release_info, series_id,
                             episode_id)

        if media_type == 'series':
            use_pp_threshold = settings.general.use_postprocessing_threshold
            pp_threshold = int(settings.general.postprocessing_threshold)
        else:
            use_pp_threshold = settings.general.use_postprocessing_threshold_movie
            pp_threshold = int(settings.general.postprocessing_threshold_movie)

        if not use_pp_threshold or (use_pp_threshold and percent_score < pp_threshold):
            logging.debug(f"BAZARR Using post-processing command: {command}")
            postprocessing(command, path)
            set_chmod(subtitles_path=downloaded_path)
        else:
            logging.debug(f"BAZARR post-processing skipped because subtitles score isn't below this "
                          f"threshold value: {pp_threshold}%")

    if media_type == 'series':
        reversed_path = path_mappings.path_replace_reverse(path)
        reversed_subtitles_path = path_mappings.path_replace_reverse(downloaded_path)
        notify_sonarr(episode_metadata.sonarrSeriesId)
        event_stream(type='series', action='update', payload=episode_metadata.sonarrSeriesId)
        event_stream(type='episode-wanted', action='delete',
                     payload=episode_metadata.sonarrEpisodeId)
        if settings.general.use_plex is True:
            if settings.plex.update_series_library is True:
                # Use specific item refresh instead of full library scan
                plex_refresh_item(episode_metadata.imdbId, is_movie=False, 
                                season=episode_metadata.season, episode=episode_metadata.episode)
            if settings.plex.set_episode_added is True:
                plex_set_episode_added_date_now(episode_metadata)
        if settings.general.use_jellyfin is True:
            if settings.jellyfin.update_series_library is True:
                jellyfin_refresh_item(episode_metadata.imdbId, is_movie=False,
                                      season=episode_metadata.season, episode=episode_metadata.episode,
                                      tvdb_id=episode_metadata.tvdbId)

    else:
        reversed_path = path_mappings.path_replace_reverse_movie(path)
        reversed_subtitles_path = path_mappings.path_replace_reverse_movie(downloaded_path)
        notify_radarr(movie_metadata.radarrId)
        event_stream(type='movie-wanted', action='delete', payload=movie_metadata.radarrId)
        if settings.general.use_plex is True:
            if settings.plex.set_movie_added is True:
                plex_set_movie_added_date_now(movie_metadata)
            if settings.plex.update_movie_library is True:
                # Use specific item refresh instead of full library scan
                plex_refresh_item(movie_metadata.imdbId, is_movie=True)
        if settings.general.use_jellyfin is True:
            if settings.jellyfin.update_movie_library is True:
                jellyfin_refresh_item(movie_metadata.imdbId, is_movie=True,
                                      tmdb_id=movie_metadata.tmdbId)

    # Call external webhook after all processing is complete if enabled
    call_external_webhook(
        subtitle_path=downloaded_path,
        media_path=path,
        language=downloaded_language,
        media_type=media_type
    )

    # Auto-translate: trigger translation to any profile language configured with translate_from
    _trigger_auto_translation(
        downloaded_lang=downloaded_language_code2,
        subtitle_path=subtitle.storage_path,
        video_path=path,
        media_type=media_type,
        series_id=series_id if media_type == 'series' else None,
        episode_id=episode_id if media_type == 'series' else None,
        radarr_id=movie_metadata.radarrId if media_type != 'series' else None,
        source_score_percent=percent_score,
    )

    event_tracker.track_subtitles(provider=downloaded_provider, action=action, language=downloaded_language)

    return ProcessSubtitlesResult(message=message,
                                  reversed_path=reversed_path,
                                  downloaded_language_code2=downloaded_language_code2,
                                  downloaded_provider=downloaded_provider,
                                  score=subtitle.score,
                                  forced=subtitle.language.forced,
                                  subtitle_id=subtitle.id,
                                  reversed_subtitles_path=reversed_subtitles_path,
                                  hearing_impaired=subtitle.language.hi,
                                  matched=list(subtitle.matches or []),
                                  not_matched=_get_not_matched(subtitle, media_type)),


def _get_not_matched(subtitle, media_type):
    _, _, scores = _get_scores(media_type)

    if subtitle.matches and isinstance(subtitle.matches, set) and 'hash' not in subtitle.matches:
        return list(set(scores) - set(subtitle.matches))
    else:
        return []
