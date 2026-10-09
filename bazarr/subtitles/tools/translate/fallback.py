# coding=utf-8

import ast
import logging
import os

from app.config import settings
from app.database import (TableEpisodes, TableShows, TableMovies, database, select, get_subtitles,
                          get_audio_profile_languages, get_profiles_list)
from app.jobs_queue import jobs_queue
from utilities.path_mappings import path_mappings
from subtitles.embedded import extract_embedded_subtitle

from .main import translate_subtitles_file


def _qualifiers_match(sub, target_forced, target_hi):
    # A forced target needs a forced source (full-dialog subtitles would translate to the wrong
    # thing) and a forced source only covers part of the dialog, so it cannot serve a full target.
    if target_forced:
        return bool(sub['forced'])
    if sub['forced']:
        return False
    # An HI target needs an HI source: translation cannot synthesize the sound cues.
    if target_hi:
        return bool(sub['hi'])
    return True


def pick_translation_source(subtitles, target_language, audio_languages, preferred_from=None,
                            forced=False, hi=False):
    """Choose the best available subtitle to translate ``target_language`` from.

    Candidates come from the list returned by ``get_subtitles(...)``: external subtitles
    (``path`` set) and embedded tracks (``embedded_track_id`` set, extracted on demand).
    Preference order for the source language:

    1. one of ``preferred_from`` (in the order the user listed them)
    2. one of ``audio_languages`` (in audio-track order)
    3. any other language

    Within the same language, an external file is preferred over an embedded track (it
    skips an extraction step). The source qualifiers must match the requested target:
    a *forced* target (foreign parts only) needs a *forced* source since full-dialog
    subtitles would translate to the wrong thing, and conversely a *forced* source is
    never picked for a full target. A *hearing-impaired* target needs a
    *hearing-impaired* source (translation carries the sound cues over, it cannot add
    them), while a full target accepts hearing-impaired sources (they are full
    translations). A source in the target language itself is obviously skipped.

    :param subtitles: subtitles rows as returned by ``get_subtitles``
    :param target_language: alpha2 code of the language to translate to
    :param audio_languages: list of alpha2 codes of the media audio tracks
    :param preferred_from: optional ordered list of preferred source alpha2 codes
    :param forced: the missing entry requests forced subtitles
    :param hi: the missing entry requests hearing-impaired subtitles
    :return: the chosen subtitles row, or ``None`` when no viable source exists
    """
    preferred = [str(x).lower() for x in (preferred_from or [])]
    audio = [str(x).lower() for x in (audio_languages or [])]
    target = target_language.lower()

    candidates = [s for s in subtitles
                  if s['code2'] and s['code2'].lower() != target
                  and _qualifiers_match(s, forced, hi)]

    def rank(sub):
        lang = sub['code2'].lower()
        if lang in preferred:
            language_rank = preferred.index(lang)
        elif lang in audio:
            language_rank = len(preferred) + audio.index(lang)
        else:
            language_rank = len(preferred) + len(audio) + 1
        # external (path set) beats embedded (needs extraction) within the same language
        return (language_rank, 0 if sub['path'] else 1, sub['code2'])

    viable = sorted(candidates, key=rank)
    return viable[0] if viable else None


def extract_and_translate_embedded(subtitles_id, media_type, to_lang, video_path, from_lang,
                                   forced=False, hi=False, sonarr_series_id=None, sonarr_episode_id=None,
                                   radarr_id=None, job_id=None):
    """Job that extracts an embedded subtitles track then translates the extracted file."""
    if not job_id:
        jobs_queue.add_job_from_function(f'Extracting and translating to {to_lang.upper()} '
                                         f'using {settings.translator.translator_type.replace("_", " ").title()}',
                                         is_progress=True)
        return

    subtitles_path = extract_embedded_subtitle(subtitles_id=subtitles_id, media_type=media_type, job_id=job_id)
    if not subtitles_path:
        return

    translate_subtitles_file(video_path=video_path,
                             source_srt_file=subtitles_path,
                             from_lang=from_lang,
                             to_lang=to_lang,
                             forced=forced,
                             hi=hi,
                             media_type=media_type,
                             sonarr_series_id=sonarr_series_id,
                             sonarr_episode_id=sonarr_episode_id,
                             radarr_id=radarr_id,
                             metadata=None,
                             job_id=job_id)


def auto_translate_missing(sonarr_episode_id=None, radarr_id=None):
    """Enqueue translations for languages still missing after a search came up empty.

    For every language still listed as missing, pick the best matching source subtitle
    (external file, or embedded track which gets extracted first) and enqueue a
    translation job with the configured translator. Forced and hearing-impaired
    variants are only translated from a source carrying the same qualifier, since
    translation cannot synthesize or drop those traits. No-op unless the media's
    languages profile has *auto translate* enabled.

    :param sonarr_episode_id: episode to translate missing subtitles for
    :param radarr_id: movie to translate missing subtitles for
    """
    if sonarr_episode_id:
        media_type = 'episode'
        details = database.execute(
            select(TableEpisodes.sonarrEpisodeId,
                   TableEpisodes.sonarrSeriesId,
                   TableShows.profileId,
                   TableEpisodes.missing_subtitles,
                   TableEpisodes.audio_language,
                   TableEpisodes.path,
                   TableShows.title.label('seriesTitle'),
                   TableShows.imdbId,
                   TableShows.tvdbId,
                   TableEpisodes.season,
                   TableEpisodes.episode,
                   TableEpisodes.title)
            .join(TableShows, TableShows.sonarrSeriesId == TableEpisodes.sonarrSeriesId)
            .where(TableEpisodes.sonarrEpisodeId == sonarr_episode_id)) \
            .first()
    elif radarr_id:
        media_type = 'movie'
        details = database.execute(
            select(TableMovies.radarrId,
                   TableMovies.profileId,
                   TableMovies.missing_subtitles,
                   TableMovies.audio_language,
                   TableMovies.path,
                   TableMovies.title,
                   TableMovies.imdbId,
                   TableMovies.tmdbId,
                   TableMovies.year)
            .where(TableMovies.radarrId == radarr_id)) \
            .first()
    else:
        return

    if not details:
        return

    # get_profiles_list returns the full list (not a dict) when the profile id
    # is stale, and None-ish values simply mean the flag is off
    profile = get_profiles_list(details.profileId) if details.profileId else None
    if not isinstance(profile, dict) or not profile.get('autoTranslate'):
        return

    if media_type == 'episode':
        video_path = path_mappings.path_replace(details.path)
    else:
        video_path = path_mappings.path_replace_movie(details.path)

    if not os.path.isfile(video_path):
        logging.debug(f"BAZARR skipping automatic translation, media file not found: {video_path}")
        return

    subtitles = get_subtitles(sonarr_episode_id=sonarr_episode_id, radarr_id=radarr_id)
    audio_languages = [x['code2'] for x in get_audio_profile_languages(details.audio_language)]
    preferred_from = settings.translator.auto_translate_from

    for language in ast.literal_eval(details.missing_subtitles or '[]'):
        # entries are plain alpha2 codes, optionally suffixed with qualifiers: 'fr:forced', 'fr:hi'
        qualifiers = language.lower().split(':')
        base_language = qualifiers[0]
        target_forced = 'forced' in qualifiers[1:]
        target_hi = 'hi' in qualifiers[1:]

        source = pick_translation_source(subtitles, base_language, audio_languages, preferred_from,
                                         forced=target_forced, hi=target_hi)
        if not source:
            logging.debug(f"BAZARR no source subtitle available to translate {language} for {video_path}")
            continue

        from_lang = source['code2']
        if media_type == 'episode':
            media_title = f'{details.seriesTitle} - S{details.season:02d}E{details.episode:02d}'
            sonarr_series_id = details.sonarrSeriesId
        else:
            media_title = f'{details.title} ({details.year})'
            sonarr_series_id = None

        if source['path']:
            if not os.path.isfile(source['path']):
                logging.debug(f"BAZARR skipping translation source, file not found: {source['path']}")
                continue
            logging.info(f"BAZARR translating {media_title} subtitles from {from_lang} to {language} "
                         f"as no download was found")
            translate_subtitles_file(video_path=video_path,
                                     source_srt_file=source['path'],
                                     from_lang=from_lang,
                                     to_lang=base_language,
                                     forced=target_forced,
                                     hi=target_hi,
                                     media_type=media_type,
                                     sonarr_series_id=sonarr_series_id,
                                     sonarr_episode_id=sonarr_episode_id,
                                     radarr_id=radarr_id,
                                     metadata=None)
        else:
            logging.info(f"BAZARR extracting and translating {media_title} embedded subtitles from {from_lang} "
                         f"to {language} as no download was found")
            extract_and_translate_embedded(subtitles_id=source['id'],
                                           media_type=media_type,
                                           to_lang=base_language,
                                           video_path=video_path,
                                           from_lang=from_lang,
                                           forced=target_forced,
                                           hi=target_hi,
                                           sonarr_series_id=sonarr_series_id,
                                           sonarr_episode_id=sonarr_episode_id,
                                           radarr_id=radarr_id)
