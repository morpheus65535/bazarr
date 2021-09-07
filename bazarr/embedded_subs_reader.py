# coding=utf-8

import logging
import os
import pickle
from knowit import api
import enzyme
from enzyme.exceptions import MalformedMKVError
from enzyme.exceptions import MalformedMKVError
from custom_lang import CustomLanguage
from database import TableEpisodes, TableMovies

logger = logging.getLogger(__name__)


def _handle_alpha3(detected_language: dict):
    alpha3 = detected_language["language"].alpha3
    custom = CustomLanguage.from_value(alpha3, "official_alpha3")

    if custom and custom.ffprobe_found(detected_language):
        logger.debug("Custom embedded language found: %s", custom.name)
        return custom.alpha3

    return alpha3


def embedded_subs_reader(file, file_size, media_type, use_cache=True):
    data = parse_video_metadata(file, file_size, media_type, use_cache=use_cache)

    subtitles_list = []
    if data["ffprobe"] and "subtitle" in data["ffprobe"]:
        for detected_language in data["ffprobe"]["subtitle"]:
            if not "language" in detected_language:
                continue

            # Avoid commentary subtitles
            name = detected_language.get("name", "").lower()
            if "commentary" in name:
                logging.debug("Ignoring commentary subtitle: %s", name)
                continue

            language = _handle_alpha3(detected_language)

            forced = detected_language.get("forced", False)
            hearing_impaired = detected_language.get("hearing_impaired", False)
            codec = detected_language.get("format")  # or None
            subtitles_list.append([language, forced, hearing_impaired, codec])

    elif data["enzyme"]:
        for subtitle_track in data["enzyme"].subtitle_tracks:
            hearing_impaired = (
                subtitle_track.name and "sdh" in subtitle_track.name.lower()
            )

            subtitles_list.append(
                [
                    subtitle_track.language,
                    subtitle_track.forced,
                    hearing_impaired,
                    subtitle_track.codec_id,
                ]
            )

    return subtitles_list


def parse_video_metadata(file, file_size, media_type, use_cache=True):
    # Define default data keys value
    data = {
        "ffprobe": {},
        "enzyme": {},
        "file_size": file_size,
    }

    if use_cache:
        # Get the actual cache value form database
        if media_type == 'episode':
            cache_key = TableEpisodes.select(TableEpisodes.ffprobe_cache)\
                .where(TableEpisodes.path == file)\
                .dicts()\
                .get()
        elif media_type == 'movie':
            cache_key = TableMovies.select(TableMovies.ffprobe_cache)\
                .where(TableMovies.path == file)\
                .dicts()\
                .get()
        else:
            cache_key = None

        # check if we have a value for that cache key
        try:
            # Unpickle ffprobe cache
            cached_value = pickle.loads(cache_key['ffprobe_cache'])
        except:
            pass
        else:
            # Check if file size and file id matches and if so, we return the cached value
            if cached_value['file_size'] == file_size:
                return cached_value

    # if not, we retrieve the metadata from the file
    from utils import get_binary

    ffprobe_path = get_binary("ffprobe")

    # if we have ffprobe available
    if ffprobe_path:
        api.initialize({"provider": "ffmpeg", "ffmpeg": ffprobe_path})
        data["ffprobe"] = api.know(file)
    # if not, we use enzyme for mkv files
    else:
        if os.path.splitext(file)[1] == ".mkv":
            with open(file, "rb") as f:
                try:
                    mkv = enzyme.MKV(f)
                except MalformedMKVError:
                    logger.error(
                        "BAZARR cannot analyze this MKV with our built-in MKV parser, you should install "
                        "ffmpeg/ffprobe: " + file
                    )
                else:
                    data["enzyme"] = mkv

    # we write to db the result and return the newly cached ffprobe dict
    if media_type == 'episode':
        TableEpisodes.update({TableEpisodes.ffprobe_cache: pickle.dumps(data, pickle.HIGHEST_PROTOCOL)})\
            .where(TableEpisodes.path == file)\
            .execute()
    elif media_type == 'movie':
        TableMovies.update({TableEpisodes.ffprobe_cache: pickle.dumps(data, pickle.HIGHEST_PROTOCOL)})\
            .where(TableMovies.path == file)\
            .execute()
    return data
