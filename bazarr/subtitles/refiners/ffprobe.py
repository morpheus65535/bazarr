# coding=utf-8
# fmt: off

import logging

from subliminal import Movie

from utilities.path_mappings import path_mappings
from app.database import TableEpisodes, TableMovies
from utilities.video_analyzer import parse_video_metadata


def refine_from_ffprobe(path, video):
    if isinstance(video, Movie):
        file_id = TableMovies.select(TableMovies.movie_file_id, TableMovies.file_size)\
            .where(TableMovies.path == path_mappings.path_replace_reverse_movie(path))\
            .dicts()\
            .get_or_none()
    else:
        file_id = TableEpisodes.select(TableEpisodes.episode_file_id, TableEpisodes.file_size)\
            .where(TableEpisodes.path == path_mappings.path_replace_reverse(path))\
            .dicts()\
            .get_or_none()

    if not file_id:
        return video

    if isinstance(video, Movie):
        data = parse_video_metadata(file=path, file_size=file_id['file_size'],
                                    movie_file_id=file_id['movie_file_id'])
    else:
        data = parse_video_metadata(file=path, file_size=file_id['file_size'],
                                    episode_file_id=file_id['episode_file_id'])

    if not data or ('ffprobe' not in data and 'mediainfo' not in data):
        logging.debug("No cache available for this file: {}".format(path))
        return video

    if data['ffprobe']:
        logging.debug('FFprobe found: %s', data['ffprobe'])
        parser_data = data['ffprobe']
    elif data['mediainfo']:
        logging.debug('Mediainfo found: %s', data['mediainfo'])
        parser_data = data['mediainfo']
    else:
        parser_data = {}

    if 'video' not in parser_data:
        logging.debug('BAZARR parser was unable to find video tracks in the file!')
    else:
        if 'resolution' in parser_data['video'][0]:
            if not video.resolution:
                video.resolution = parser_data['video'][0]['resolution']
        if 'codec' in parser_data['video'][0]:
            if not video.video_codec:
                video.video_codec = parser_data['video'][0]['codec']
        if 'frame_rate' in parser_data['video'][0]:
            if not video.fps:
                if isinstance(parser_data['video'][0]['frame_rate'], float):
                    video.fps = parser_data['video'][0]['frame_rate']
                else:
                    try:
                        video.fps = parser_data['video'][0]['frame_rate'].magnitude
                    except AttributeError:
                        video.fps = parser_data['video'][0]['frame_rate']

    if 'audio' not in parser_data:
        logging.debug('BAZARR parser was unable to find audio tracks in the file!')
    else:
        if 'codec' in parser_data['audio'][0]:
            if not video.audio_codec:
                video.audio_codec = parser_data['audio'][0]['codec']
        for track in parser_data['audio']:
            if 'language' in track:
                video.audio_languages.add(track['language'].alpha3)

    return video
