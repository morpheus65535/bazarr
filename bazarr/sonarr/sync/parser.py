# coding=utf-8

import os
from datetime import datetime

from dateutil import parser

from app.config import settings
from app.database import TableShows, database, select
from constants import MINIMUM_VIDEO_SIZE
from languages.get_languages import audio_language_from_name
from utilities.path_mappings import path_mappings
from utilities.video_analyzer import embedded_audio_reader
from sonarr.info import get_sonarr_info
from sonarr.series_snapshot import Series, SeriesValues
from utilities.arr_sync_lookups import ArrSyncLookups
from utilities.media_codecs import sonarr_audio_codec, sonarr_video_codec
from sonarr.episode_snapshot import Episode, EpisodeFile, EpisodeValues


def seriesParser(show: Series, action: str, lookups: ArrSyncLookups,
                 serie_default_profile: int | None) -> SeriesValues:
    """Return TableShows column values for a Sonarr series."""
    overview = show.overview
    poster = ''
    fanart = ''
    for image in show.images:
        if image.coverType == 'poster':
            poster_big = image.url.split('?')[0]
            poster = f'{os.path.splitext(poster_big)[0]}-250{os.path.splitext(poster_big)[1]}'

        if image.coverType == 'fanart':
            fanart = image.url.split('?')[0]

    if show.alternateTitles is not None:
        alternate_titles = [item.title for item in show.alternateTitles if item.title not
                            in [None, ''] and item.title != show.title]
    else:
        alternate_titles = []

    tags = lookups.tags(show.tags)

    imdbId = show.imdbId

    tmdbId = show.tmdbId or None

    ended = 'True' if show.ended else 'False'

    lastAired = None
    if show.lastAired:
        aired = parser.parse(show.lastAired)
        if not isinstance(aired, datetime):
            raise ValueError('Invalid last-aired date')
        lastAired = aired.strftime('%Y-%m-%d')

    original = show.originalLanguage
    original_language = original.name if original is not None else None

    audio_language = []
    general_settings = settings.general
    if not general_settings.parse_embedded_audio_track:
        if get_sonarr_info.is_legacy():
            audio_language = lookups.audio_languages(show.qualityProfileId)
        else:
            if show.languageProfileId is not None:
                audio_language = lookups.audio_languages(show.languageProfileId)
            else:
                audio_language = []

    parsed_series: SeriesValues = {
        'title': show.title,
        'path': show.path,
        'tvdbId': int(show.tvdbId),
        'sonarrSeriesId': int(show.id),
        'overview': overview,
        'poster': poster,
        'fanart': fanart,
        'audio_language': str(audio_language),
        'sortTitle': show.sortTitle,
        'year': str(show.year),
        'alternativeTitles': str(alternate_titles),
        'tags': str(tags),
        'seriesType': show.seriesType,
        'imdbId': imdbId,
        'tmdbId': tmdbId,
        'monitored': str(bool(show.monitored)),
        'ended': ended,
        'lastAired': lastAired,
        'originalLanguage': original_language,
    }

    if action == 'insert':
        parsed_series['profileId'] = serie_default_profile
    
    if general_settings.serie_tag_enabled:
        tag_profile = lookups.matching_profile(tags)
        if tag_profile:
            parsed_series['profileId'] = tag_profile
        remove_profile_tags_list = general_settings.remove_profile_tags
        if len(remove_profile_tags_list) > 0:
            if set(tags) & set(remove_profile_tags_list):
                parsed_series['profileId'] = None

    return parsed_series


def get_episode_file_size(file: EpisodeFile) -> int:
    if file.size > MINIMUM_VIDEO_SIZE:
        return file.size
    try:
        return os.path.getsize(path_mappings.path_replace(file.path))
    except OSError:
        return 0


def episodeParser(episode: Episode, parse_embedded_audio_track: bool | None = None,
                  *, audio_languages: dict[int, str | None] | None = None,
                  file_size: int | None = None) -> EpisodeValues | None:
    general_settings = settings.general
    file = episode.episodeFile
    if not episode.hasFile or file is None:
        return None
    if file_size is None:
        file_size = get_episode_file_size(file)
    if not (file_size > MINIMUM_VIDEO_SIZE or
            (general_settings.enable_strm_support and file.path.lower().endswith('.strm'))):
        return None
    if parse_embedded_audio_track is None:
        parse_embedded_audio_track = general_settings.parse_embedded_audio_track
    audio_language: list[str | None] | str | None
    if parse_embedded_audio_track:
        audio_language = embedded_audio_reader(path_mappings.path_replace(file.path),
                                               file_size=file.size, episode_file_id=file.id, use_cache=True)
    else:
        language = file.language
        languages = file.languages
        if language:
            audio_language = [audio_language_from_name(language.name)]
        elif languages:
            audio_language = [audio_language_from_name(language.name) for language in languages]
        else:
            series_id = episode.seriesId
            if audio_languages is None:
                audio_languages = {}
            if series_id not in audio_languages:
                audio_languages[series_id] = database.execute(select(TableShows.audio_language)
                                                              .where(TableShows.sonarrSeriesId == series_id)).scalar()
            audio_language = audio_languages[series_id]
    media_info = file.mediaInfo
    video_codec = sonarr_video_codec(media_info.videoCodec) if media_info else None
    audio_codec = sonarr_audio_codec(media_info.audioCodec) if media_info else None
    quality = file.quality.quality
    try:
        video_format, video_resolution = quality.name.split('-')
    except ValueError:
        video_format = quality.name
        resolution = quality.resolution
        video_resolution = f'{resolution}p' if resolution is not None else None
    return {'sonarrSeriesId': episode.seriesId,
            'sonarrEpisodeId': episode.id,
            'title': episode.title,
            'path': file.path,
            'season': episode.seasonNumber,
            'episode': episode.episodeNumber,
            'sceneName': file.sceneName,
            'monitored': str(episode.monitored),
            'format': video_format,
            'resolution': video_resolution,
            'video_codec': video_codec,
            'audio_codec': audio_codec,
            'episode_file_id': file.id,
            'audio_language': str(audio_language),
            'file_size': file.size,
            'absoluteEpisode': episode.absoluteEpisodeNumber,
            'tvdbId': episode.tvdbId}
