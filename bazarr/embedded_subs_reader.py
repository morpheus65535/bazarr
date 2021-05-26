# coding=utf-8

import logging
import os
import pickle
from knowit import api
import enzyme
from enzyme.exceptions import MalformedMKVError
from enzyme.exceptions import MalformedMKVError
from database import TableEpisodes, TableMovies

_FFPROBE_SPECIAL_LANGS = {
    "zho": {
        "list": ["cht", "tc", "traditional", "zht", "hant", "big5", u"繁", u"雙語"],
        "alpha3": "zht",
    },
    "por": {
        "list": ["pt-br", "pob", "pb", "brazilian", "brasil", "brazil"],
        "alpha3": "pob",
    },
}

def _handle_alpha3(detected_language: dict):
    alpha3 = detected_language["language"].alpha3

    name = detected_language.get("name", "").lower()
    special_lang = _FFPROBE_SPECIAL_LANGS.get(alpha3)

    if special_lang is None or not name:
        return alpha3  # The original alpha3

    if any(ext in name for ext in special_lang["list"]):
        return special_lang["alpha3"]  # Guessed alpha from _FFPROBE_OTHER_LANGS

    return alpha3  # In any case

def embedded_subs_reader(file, file_size, episode_file_id=None, movie_file_id=None):
    data = parse_video_metadata(file, file_size, episode_file_id, movie_file_id)

    subtitles_list = []
    if data['ffprobe'] and 'subtitle' in data['ffprobe']:
        for detected_language in data['ffprobe']['subtitle']:
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
            codec = detected_language.get("format") # or None
            subtitles_list.append([language, forced, hearing_impaired, codec])

    elif data['enzyme']:
        for subtitle_track in data['enzyme'].subtitle_tracks:
            hearing_impaired = subtitle_track.name and "sdh" in subtitle_track.name.lower()

            subtitles_list.append([subtitle_track.language, subtitle_track.forced, hearing_impaired,
                                   subtitle_track.codec_id])

    return subtitles_list


def parse_video_metadata(file, file_size, episode_file_id=None, movie_file_id=None):
    # Define default data keys value
    data = {
        'ffprobe': {},
        'enzyme': {},
        'file_id': episode_file_id or movie_file_id,
        'file_size': file_size
    }

    # Get the actual cache value form database
    if episode_file_id:
        cache_key = TableEpisodes.select(TableEpisodes.ffprobe_cache)\
            .where((TableEpisodes.episode_file_id == episode_file_id) and
                   (TableEpisodes.file_size == file_size))\
            .dicts()\
            .get()
    elif movie_file_id:
        cache_key = TableMovies.select(TableMovies.ffprobe_cache)\
            .where(TableMovies.movie_file_id == movie_file_id and
                   TableMovies.file_size == file_size)\
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
        if cached_value['file_size'] == file_size and cached_value['file_id'] in [episode_file_id, movie_file_id]:
            return cached_value

    # if not, we retrieve the metadata from the file
    from utils import get_binary
    ffprobe_path = get_binary("ffprobe")

    # if we have ffprobe available
    if ffprobe_path:
        api.initialize({'provider': 'ffmpeg', 'ffmpeg': ffprobe_path})
        data['ffprobe'] = api.know(file)
    # if nto, we use enzyme for mkv files
    else:
        if os.path.splitext(file)[1] == '.mkv':
            with open(file, 'rb') as f:
                try:
                    mkv = enzyme.MKV(f)
                except MalformedMKVError:
                    logging.error(
                        'BAZARR cannot analyze this MKV with our built-in MKV parser, you should install '
                        'ffmpeg/ffprobe: ' + file)
                else:
                    data['enzyme'] = mkv

    # we write to db the result and return the newly cached ffprobe dict
    if episode_file_id:
        TableEpisodes.update({TableEpisodes.ffprobe_cache: pickle.dumps(data, pickle.HIGHEST_PROTOCOL)})\
            .where(TableEpisodes.episode_file_id == episode_file_id)\
            .execute()
    elif movie_file_id:
        TableMovies.update({TableEpisodes.ffprobe_cache: pickle.dumps(data, pickle.HIGHEST_PROTOCOL)})\
            .where(TableMovies.movie_file_id == movie_file_id)\
            .execute()
    return data
