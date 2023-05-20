# coding=utf-8

import logging
import pickle

from knowit.api import know, KnowitException

from languages.custom_lang import CustomLanguage
from languages.get_languages import language_from_alpha3, alpha3_from_alpha2
from app.database import TableEpisodes, TableMovies, database, update, select
from utilities.path_mappings import path_mappings
from app.config import settings


def _handle_alpha3(detected_language: dict):
    alpha3 = detected_language["language"].alpha3
    custom = CustomLanguage.from_value(alpha3, "official_alpha3")

    if not custom:
        return alpha3

    found = custom.language_found(detected_language["language"])
    if not found:
        found = custom.ffprobe_found(detected_language)

    if found:
        logging.debug("Custom embedded language found: %s", custom.name)
        return custom.alpha3

    return alpha3

def embedded_subs_reader(file, file_size, episode_file_id=None, movie_file_id=None, use_cache=True):
    data = parse_video_metadata(file, file_size, episode_file_id, movie_file_id, use_cache=use_cache)
    und_default_language = alpha3_from_alpha2(settings.general.default_und_embedded_subtitles_lang)

    subtitles_list = []

    if not data:
        return subtitles_list

    cache_provider = None
    if "ffprobe" in data and data["ffprobe"] and "subtitle" in data["ffprobe"]:
        cache_provider = 'ffprobe'
    elif 'mediainfo' in data and data["mediainfo"] and "subtitle" in data["mediainfo"]:
        cache_provider = 'mediainfo'

    if cache_provider:
        for detected_language in data[cache_provider]["subtitle"]:
            # Avoid commentary subtitles
            name = detected_language.get("name", "").lower()
            if "commentary" in name:
                logging.debug(f"Ignoring commentary subtitle: {name}")
                continue

            if "language" not in detected_language:
                language = None
            else:
                language = _handle_alpha3(detected_language)

            if not language and und_default_language:
                logging.debug(f"Undefined language embedded subtitles track treated as {language}")
                language = und_default_language

            if not language:
                continue

            forced = detected_language.get("forced", False)
            hearing_impaired = detected_language.get("hearing_impaired", False)
            codec = detected_language.get("format")  # or None
            subtitles_list.append([language, forced, hearing_impaired, codec])

    return subtitles_list


def embedded_audio_reader(file, file_size, episode_file_id=None, movie_file_id=None, use_cache=True):
    data = parse_video_metadata(file, file_size, episode_file_id, movie_file_id, use_cache=use_cache)

    audio_list = []

    if not data:
        return audio_list

    cache_provider = None
    if "ffprobe" in data and data["ffprobe"] and "audio" in data["ffprobe"]:
        cache_provider = 'ffprobe'
    elif 'mediainfo' in data and data["mediainfo"] and "audio" in data["mediainfo"]:
        cache_provider = 'mediainfo'

    if cache_provider:
        for detected_language in data[cache_provider]["audio"]:
            if "language" not in detected_language:
                audio_list.append(None)
                continue

            alpha3 = _handle_alpha3(detected_language)
            language = language_from_alpha3(alpha3)

            if language not in audio_list:
                audio_list.append(language)

    return audio_list


def parse_video_metadata(file, file_size, episode_file_id=None, movie_file_id=None, use_cache=True):
    # Define default data keys value
    data = {
        "ffprobe": {},
        "mediainfo": {},
        "file_id": episode_file_id or movie_file_id,
        "file_size": file_size,
    }

    embedded_subs_parser = settings.general.embedded_subtitles_parser

    if use_cache:
        # Get the actual cache value form database
        if episode_file_id:
            cache_key = database.execute(
                select(TableEpisodes.ffprobe_cache)
                .where(TableEpisodes.path == path_mappings.path_replace_reverse(file))) \
                .first()
        elif movie_file_id:
            cache_key = database.execute(
                select(TableMovies.ffprobe_cache)
                .where(TableMovies.path == path_mappings.path_replace_reverse_movie(file))) \
                .first()
        else:
            cache_key = None

        # check if we have a value for that cache key
        try:
            # Unpickle ffprobe cache
            cached_value = pickle.loads(cache_key.ffprobe_cache)
        except Exception:
            pass
        else:
            # Check if file size and file id matches and if so, we return the cached value if available for the
            # desired parser
            if cached_value['file_size'] == file_size and cached_value['file_id'] in [episode_file_id, movie_file_id]:
                if embedded_subs_parser in cached_value and cached_value[embedded_subs_parser]:
                    return cached_value
                else:
                    # no valid cache
                    pass
            else:
                # cache must be renewed
                pass

    # if not, we retrieve the metadata from the file
    from utilities.binaries import get_binary

    ffprobe_path = mediainfo_path = None
    if embedded_subs_parser == 'ffprobe':
        ffprobe_path = get_binary("ffprobe")
    elif embedded_subs_parser == 'mediainfo':
        mediainfo_path = get_binary("mediainfo")

    # if we have ffprobe available
    if ffprobe_path:
        try:
            data["ffprobe"] = know(video_path=file, context={"provider": "ffmpeg", "ffmpeg": ffprobe_path})
        except KnowitException as e:
            logging.error(f"BAZARR ffprobe cannot analyze this video file {file}. Could it be corrupted? {e}")
            return None
    # or if we have mediainfo available
    elif mediainfo_path:
        try:
            # disabling mediainfo path temporarily until issue with knowit is fixed.
            # data["mediainfo"] = know(video_path=file, context={"provider": "mediainfo", "mediainfo": mediainfo_path})
            data["mediainfo"] = know(video_path=file, context={"provider": "mediainfo"})
        except KnowitException as e:
            logging.error(f"BAZARR mediainfo cannot analyze this video file {file}. Could it be corrupted? {e}")
            return None
    # else, we warn user of missing binary
    else:
        logging.error("BAZARR require ffmpeg/ffprobe or mediainfo, please install it and make sure to choose it in "
                      "Settings-->Subtitles.")
        return

    # we write to db the result and return the newly cached ffprobe dict
    if episode_file_id:
        database.execute(
            update(TableEpisodes)
            .values(ffprobe_cache=pickle.dumps(data, pickle.HIGHEST_PROTOCOL))
            .where(TableEpisodes.path == path_mappings.path_replace_reverse(file)))
    elif movie_file_id:
        database.execute(
            update(TableMovies)
            .values(ffprobe_cache=pickle.dumps(data, pickle.HIGHEST_PROTOCOL))
            .where(TableMovies.path == path_mappings.path_replace_reverse_movie(file)))
    return data
