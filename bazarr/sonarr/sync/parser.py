# coding=utf-8

import os
from datetime import datetime

import msgspec

from dateutil import parser

from app.config import settings
from app.database import TableShows, database, select
from constants import MINIMUM_VIDEO_SIZE
from languages.get_languages import audio_language_from_name
from utilities.path_mappings import path_mappings
from utilities.video_analyzer import embedded_audio_reader
from sonarr.info import get_sonarr_info
from sonarr.series_snapshot import Series, SeriesValues
from utilities.arr_types import ArrTag
from sonarr.episode_snapshot import Episode, EpisodeValues

from .converter import SonarrFormatVideoCodec, SonarrFormatAudioCodec


def get_matching_profile(tags, language_profiles):
    matching_profile = None
    if len(tags) > 0:
        for profileId, name, tag in language_profiles:
            if tag in tags:
                matching_profile = profileId
                break
    return matching_profile


def seriesParser(show, action, tags_dict, language_profiles, serie_default_profile, audio_profiles):
    """Convert a Sonarr series payload into the column values of ``TableShows``.

    :param dict show: series payload returned by the Sonarr API.
    :param str action: ``'insert'`` also assigns the default language profile.
    :param list tags_dict: Sonarr tag definitions as returned by the API.
    :param list language_profiles: language profiles as ``(profileId, name, tag)`` tuples.
    :param int serie_default_profile: profile ID assigned to new series.
    :param list audio_profiles: audio profiles as ``(profileId, name)`` tuples.
    :return: column name to value mapping, ready for insert or update.
    :rtype: dict
    """
    overview = show['overview'] if 'overview' in show else ''
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

    tags = [d['label'] for d in tags_dict if d['id'] in show.tags]

    imdbId = show.imdbId

    tmdbId = show.tmdbId

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
            audio_language = profile_id_to_language(show.qualityProfileId, audio_profiles)
        else:
            if show.languageProfileId is not msgspec.UNSET:
                audio_language = profile_id_to_language(show.languageProfileId, audio_profiles)
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
        tag_profile = get_matching_profile(tags, language_profiles)
        if tag_profile:
            parsed_series['profileId'] = tag_profile
        remove_profile_tags_list = general_settings.remove_profile_tags
        if len(remove_profile_tags_list) > 0:
            if set(tags) & set(remove_profile_tags_list):
                parsed_series['profileId'] = None

    return parsed_series


def profile_id_to_language(id_, profiles):
    profiles_to_return = []
    for profile in profiles:
        if id_ == profile[0]:
            profiles_to_return.append(profile[1])
    return profiles_to_return


def episodeParser(episode: Episode, parse_embedded_audio_track: bool | None = None) -> EpisodeValues | None:
    general_settings = settings.general
    file = episode.episodeFile
    if not episode.hasFile or file is None:
        return None
    file_size = file.size
    if file_size <= MINIMUM_VIDEO_SIZE:
        try:
            file_size = os.path.getsize(path_mappings.path_replace(file.path))
        except OSError:
            file_size = 0
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
            audio_language = database.execute(select(TableShows.audio_language)
                                               .where(TableShows.sonarrSeriesId == series_id)).scalar()
    media_info = file.mediaInfo
    video_codec = SonarrFormatVideoCodec(media_info.videoCodec) if media_info else None
    audio_codec = SonarrFormatAudioCodec(media_info.audioCodec) if media_info else None
    quality = file.quality.quality
    try:
        video_format, video_resolution = quality.name.split('-')
    except ValueError:
        video_format = quality.name
        resolution = quality.resolution
        video_resolution = f'{resolution}p' if resolution is not msgspec.UNSET else None
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
