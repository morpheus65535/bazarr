# coding=utf-8

import logging
import os
from knowit import api
import enzyme
import pickle
from enzyme.exceptions import MalformedMKVError

from utils import get_binary
from get_languages import language_from_alpha3
from database import TableEpisodes, TableMovies
from indexer.utils import VIDEO_EXTENSION


def video_prop_reader(file, media_type, use_cache=False):
    # function to get video properties from a media file
    video_prop = {}

    if os.path.splitext(file)[1] not in VIDEO_EXTENSION:
        # unsupported file extension so we don't care about it and return an empty dict
        logging.debug(f'Unsupported file extension: {file}')
        return video_prop

    # get the ffprobe path
    ffprobe_path = get_binary("ffprobe")

    # Define default data keys value
    data = {
        "ffprobe": {},
        "enzyme": {},
        "file_size": os.stat(file).st_size,
    }

    no_cache = False
    if use_cache:
        # Get the actual cache value form database
        try:
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
        except (TableEpisodes.DoesNotExist, TableMovies.DoesNotExist):
            no_cache = True
            pass
        else:
            # check if we have a value for that cache key
            try:
                # Unpickle ffprobe cache
                cached_value = pickle.loads(cache_key['ffprobe_cache'])
            except Exception:
                pass
            else:
                # Check if file size match and if so, we return the cached value
                if cached_value['file_size'] == os.stat(file).st_size:
                    data = cached_value['ffprobe'] if ffprobe_path else cached_value['']

    if no_cache:
        # ok we wont use cache...
        # if we have ffprobe available
        if ffprobe_path:
            api.initialize({"provider": "ffmpeg", "ffmpeg": ffprobe_path})
            data = api.know(file)
        # if not, we use enzyme for mkv files
        elif not ffprobe_path and os.path.splitext(file)[1] == "mkv":
            if os.path.splitext(file)[1] == ".mkv":
                with open(file, "rb") as f:
                    try:
                        mkv = enzyme.MKV(f)
                    except MalformedMKVError:
                        logging.error(
                            "BAZARR cannot analyze this MKV with our built-in MKV parser, you should install "
                            "ffmpeg/ffprobe: " + file
                        )
                    else:
                        data = mkv
        else:
            logging.debug(f"ffprobe not available and enzyme doesn't support this file extension: {file}")

    if data:
        audio_language = []
        video_format = None
        video_resolution = None
        video_codec = None
        audio_codec = None
        file_size = os.path.getsize(file)

        if ffprobe_path:
            # if ffprobe has been used, we populate our dict using returned values
            if 'video' in data and len(data['video']):
                video_resolution = data['video'][0]['resolution']
                if 'codec' in data['video'][0]:
                    video_codec = data['video'][0]['codec']
            if 'audio' in data and len(data['audio']):
                audio_codec = data['audio'][0]['codec']
                for audio_track in data['audio']:
                    if 'language' in audio_track:
                        audio_lang = audio_track['language'].alpha3
                        if audio_lang:
                            converted_audio_lang = language_from_alpha3(audio_track['language'].alpha3)
                            if converted_audio_lang and converted_audio_lang not in audio_language:
                                audio_language.append(converted_audio_lang)
                            elif not converted_audio_lang:
                                pass
                            else:
                                pass
        elif not ffprobe_path and os.path.splitext(file)[1] == "mkv":
            # if we didn't found ffprobe but the file is an mkv, we parse enzyme metadata and populate our dict wit it.
            if len(data.video_tracks):
                for video_track in data.video_tracks:
                    video_resolution = str(video_track.height) + 'p'
                    video_codec = video_track.codec_id

            if len(data.audio_tracks):
                audio_codec = data.audio_tracks[0].codec_id
                for audio_track in data.audio_tracks:
                    audio_language.append(audio_track.name)

        video_prop['audio_language'] = str(audio_language)
        video_prop['format'] = video_format
        video_prop['resolution'] = video_resolution
        video_prop['video_codec'] = video_codec
        video_prop['audio_codec'] = audio_codec
        video_prop['file_size'] = file_size

    return video_prop
