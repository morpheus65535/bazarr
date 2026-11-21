# coding=utf-8

import os

from app.config import settings
from languages.get_languages import audio_language_from_name
from radarr.info import get_radarr_info
from radarr.movie_snapshot import Movie, MovieValues
from utilities.arr_sync_lookups import ArrSyncLookups
from utilities.video_analyzer import embedded_audio_reader
from utilities.path_mappings import path_mappings

from .converter import RadarrFormatAudioCodec, RadarrFormatVideoCodec


def movieParser(movie: Movie, action: str, lookups: ArrSyncLookups,
                movie_default_profile: int | None) -> MovieValues:
    file = movie.movieFile
    assert file is not None
    legacy = get_radarr_info.is_legacy()
    images = movie.images or []
    poster = ''
    if images:
        poster_big = images[0].url
        poster = f'{os.path.splitext(poster_big)[0]}-500{os.path.splitext(poster_big)[1]}'
    fanart = images[1].url if len(images) > 1 else ''
    titles = movie.alternativeTitles if legacy else movie.alternateTitles
    alternative_titles = str([item.title for item in titles]) if titles is not None else None
    quality = file.quality.quality
    try:
        video_format, resolution = quality.name.split('-')
    except ValueError:
        video_format = quality.name
        quality_resolution = quality.resolution
        resolution = f'{quality_resolution}p' if quality_resolution is not None else None
    media = file.mediaInfo
    if media:
        video_codec = RadarrFormatVideoCodec((media.videoFormat if legacy else media.videoCodec),
                                             media.videoCodecID, media.videoCodecLibrary)
        audio_codec = RadarrFormatAudioCodec((media.audioFormat if legacy else media.audioCodec),
                                             media.audioCodecID, media.audioProfile,
                                             media.audioAdditionalFeatures)
    else:
        video_codec = audio_codec = None
    general_settings = settings.general
    parse_audio = general_settings.parse_embedded_audio_track
    if parse_audio:
        audio_language = embedded_audio_reader(path_mappings.path_replace_movie(file.path),
                                               file_size=int(file.size), movie_file_id=file.id, use_cache=True)
    elif legacy:
        audio_languages = media.audioLanguages if media else None
        audio_language = [language.strip() for language in audio_languages.split('/')] if audio_languages is not None else []
        if not audio_language:
            audio_language = lookups.audio_languages(movie.qualityProfileId)
    else:
        audio_language = [audio_language_from_name(language.name) for language in file.languages or []]
    tags = lookups.tags(movie.tags)
    original = movie.originalLanguage
    parsed: MovieValues = {'radarrId': movie.id,
                          'title': movie.title,
                          'path': file.path,
                          'tmdbId': str(movie.tmdbId),
                          'poster': poster,
                          'fanart': fanart,
                          'audio_language': str(audio_language),
                          'sceneName': file.sceneName,
                          'monitored': str(movie.monitored),
                          'year': str(movie.year),
                          'sortTitle': movie.sortTitle,
                          'alternativeTitles': alternative_titles,
                          'format': video_format,
                          'resolution': resolution,
                          'video_codec': video_codec,
                          'audio_codec': audio_codec,
                          'overview': movie.overview,
                          'imdbId': movie.imdbId,
                          'movie_file_id': file.id,
                          'tags': str(tags),
                          'file_size': int(file.size),
                          'originalLanguage': original.name if original is not None else None}
    if action == 'insert':
        parsed['profileId'] = movie_default_profile
    if general_settings.movie_tag_enabled:
        tag_profile = lookups.matching_profile(tags)
        if tag_profile:
            parsed['profileId'] = tag_profile
        if set(tags) & set(general_settings.remove_profile_tags):
            parsed['profileId'] = None
    return parsed
