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


def seriesParser(show: Series, action: str, tags_dict: list[ArrTag], language_profiles, serie_default_profile: int | None, audio_profiles) -> SeriesValues:
    """
    Parse a Sonarr series object into a dictionary of values suitable for
    storing in the Bazarr database.

    The function extracts and normalizes metadata from the given show,
    including poster and fanart image URLs (the poster is converted to its
    250px variant and query strings are stripped), alternate titles
    (excluding empty values and the main title), tag labels resolved from
    the provided tag list, the ``ended`` flag, the formatted last-aired
    date, and the original language name. When embedded audio track parsing
    is disabled in the general settings, the audio language is resolved
    from the series quality profile (legacy Sonarr) or language profile
    (current Sonarr) using the provided audio profiles.

    When the action is ``'insert'``, the series default language profile is
    assigned. If series tag-based profile selection is enabled, a profile
    matching the series tags overrides the assigned profile, and if any of
    the series tags appear in the configured "remove profile" tag list, the
    profile is cleared.

    :param show: Series object returned by the Sonarr API.
    :param action: Action being performed on the series, such as
        ``'insert'`` or ``'update'``; affects whether the default profile
        is applied.
    :param tags_dict: List of Sonarr tags used to resolve tag identifiers
        into tag labels.
    :param language_profiles: Bazarr language profiles used to match
        series tags to a language profile.
    :param serie_default_profile: Default language profile identifier to
        assign to newly inserted series, or ``None`` if no default is set.
    :param audio_profiles: Sonarr quality or language profiles used to
        resolve the series audio language.
    :return: Dictionary containing the parsed series values ready to be
        persisted.
    :raises ValueError: If the series last-aired date cannot be parsed
        into a valid datetime.
    """
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

    tags = [d['label'] for d in tags_dict if d['id'] in show.tags]

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
