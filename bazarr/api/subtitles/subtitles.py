# coding=utf-8

import os
import sys

from flask import request
from flask_restful import Resource

from database import TableEpisodes, TableMovies
from helper import path_mappings
from ..utils import authenticate
from subsyncer import subsync
from utils import translate_subtitles_file, subtitles_apply_mods
from get_subtitle import store_subtitles, store_subtitles_movie
from config import settings


class Subtitles(Resource):
    @authenticate
    def patch(self):
        action = request.args.get('action')

        language = request.form.get('language')
        subtitles_path = request.form.get('path')
        media_type = request.form.get('type')
        id = request.form.get('id')

        if media_type == 'episode':
            subtitles_path = path_mappings.path_replace(subtitles_path)
            metadata = TableEpisodes.select(TableEpisodes.path, TableEpisodes.sonarrSeriesId)\
                .where(TableEpisodes.sonarrEpisodeId == id)\
                .dicts()\
                .get()
            video_path = path_mappings.path_replace(metadata['path'])
        else:
            subtitles_path = path_mappings.path_replace_movie(subtitles_path)
            metadata = TableMovies.select(TableMovies.path).where(TableMovies.radarrId == id).dicts().get()
            video_path = path_mappings.path_replace_movie(metadata['path'])

        if action == 'sync':
            if media_type == 'episode':
                subsync.sync(video_path=video_path, srt_path=subtitles_path,
                             srt_lang=language, media_type='series', sonarr_series_id=metadata['sonarrSeriesId'],
                             sonarr_episode_id=int(id))
            else:
                subsync.sync(video_path=video_path, srt_path=subtitles_path,
                             srt_lang=language, media_type='movies', radarr_id=id)
        elif action == 'translate':
            dest_language = language
            forced = True if request.form.get('forced') == 'true' else False
            hi = True if request.form.get('hi') == 'true' else False
            result = translate_subtitles_file(video_path=video_path, source_srt_file=subtitles_path,
                                              to_lang=dest_language,
                                              forced=forced, hi=hi)
            if result:
                if media_type == 'episode':
                    store_subtitles(path_mappings.path_replace_reverse(video_path), video_path)
                else:
                    store_subtitles_movie(path_mappings.path_replace_reverse_movie(video_path), video_path)
                return '', 200
            else:
                return '', 404
        else:
            subtitles_apply_mods(language, subtitles_path, [action])

        # apply chmod if required
        chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
            'win') and settings.general.getboolean('chmod_enabled') else None
        if chmod:
            os.chmod(subtitles_path, chmod)

        return '', 204
