# coding=utf-8
# fmt: off

import logging

from subliminal import Movie

from helper import path_mappings
from database import TableEpisodes, TableMovies
from embedded_subs_reader import parse_video_metadata


def refine_from_ffprobe(path, video):
    if isinstance(video, Movie):
        file_id = TableMovies.select(TableMovies.movie_file_id, TableMovies.file_size)\
            .where(TableMovies.path == path_mappings.path_replace_reverse_movie(path))\
            .dicts()\
            .get()
    else:
        file_id = TableEpisodes.select(TableEpisodes.episode_file_id, TableEpisodes.file_size)\
            .where(TableEpisodes.path == path_mappings.path_replace_reverse(path))\
            .dicts()\
            .get()

    if not isinstance(file_id, dict):
        return video

    if isinstance(video, Movie):
        data = parse_video_metadata(file=path, file_size=file_id['file_size'],
                                    movie_file_id=file_id['movie_file_id'])
    else:
        data = parse_video_metadata(file=path, file_size=file_id['file_size'],
                                    episode_file_id=file_id['episode_file_id'])

    if not data['ffprobe']:
        logging.debug("No FFprobe available in cache for this file: {}".format(path))
        return video

    logging.debug('FFprobe found: %s', data['ffprobe'])

    if 'video' not in data['ffprobe']:
        logging.debug('BAZARR FFprobe was unable to find video tracks in the file!')
    else:
        if 'resolution' in data['ffprobe']['video'][0]:
            if not video.resolution:
                video.resolution = data['ffprobe']['video'][0]['resolution']
        if 'codec' in data['ffprobe']['video'][0]:
            if not video.video_codec:
                video.video_codec = data['ffprobe']['video'][0]['codec']
        if 'frame_rate' in data['ffprobe']['video'][0]:
            if not video.fps:
                if isinstance(data['ffprobe']['video'][0]['frame_rate'], float):
                    video.fps = data['ffprobe']['video'][0]['frame_rate']
                else:
                    video.fps = data['ffprobe']['video'][0]['frame_rate'].magnitude

    if 'audio' not in data['ffprobe']:
        logging.debug('BAZARR FFprobe was unable to find audio tracks in the file!')
    else:
        if 'codec' in data['ffprobe']['audio'][0]:
            if not video.audio_codec:
                video.audio_codec = data['ffprobe']['audio'][0]['codec']
        for track in data['ffprobe']['audio']:
            if 'language' in track:
                video.audio_languages.add(track['language'].alpha3)

    return video
