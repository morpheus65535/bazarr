# coding=utf-8

import os
import sys
import gc

from flask_restx import Resource, Namespace, reqparse

from app.database import TableEpisodes, TableMovies
from languages.get_languages import alpha3_from_alpha2
from utilities.path_mappings import path_mappings
from subtitles.tools.subsyncer import SubSyncer
from subtitles.tools.translate import translate_subtitles_file
from subtitles.tools.mods import subtitles_apply_mods
from subtitles.indexer.series import store_subtitles
from subtitles.indexer.movies import store_subtitles_movie
from app.config import settings
from app.event_handler import event_stream

from ..utils import authenticate


api_ns_subtitles = Namespace('Subtitles', description='Apply mods/tools on external subtitles')


@api_ns_subtitles.route('subtitles')
class Subtitles(Resource):
    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('action', type=str, required=True,
                                      help='Action from ["sync", "translate" or mods name]')
    patch_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    patch_request_parser.add_argument('path', type=str, required=True, help='Subtitles file path')
    patch_request_parser.add_argument('type', type=str, required=True, help='Media type from ["episode", "movie"]')
    patch_request_parser.add_argument('id', type=int, required=True, help='Episode ID')
    patch_request_parser.add_argument('forced', type=str, required=False, help='Forced subtitles from ["True", "False"]')
    patch_request_parser.add_argument('hi', type=str, required=False, help='HI subtitles from ["True", "False"]')
    patch_request_parser.add_argument('original_format', type=str, required=False,
                                      help='Use original subtitles format from ["True", "False"]')

    @authenticate
    @api_ns_subtitles.doc(parser=patch_request_parser)
    @api_ns_subtitles.response(204, 'Success')
    @api_ns_subtitles.response(401, 'Not Authenticated')
    @api_ns_subtitles.response(404, 'Episode/movie not found')
    def patch(self):
        """Apply mods/tools on external subtitles"""
        args = self.patch_request_parser.parse_args()
        action = args.get('action')

        language = args.get('language')
        subtitles_path = args.get('path')
        media_type = args.get('type')
        id = args.get('id')

        if media_type == 'episode':
            metadata = TableEpisodes.select(TableEpisodes.path, TableEpisodes.sonarrSeriesId)\
                .where(TableEpisodes.sonarrEpisodeId == id)\
                .dicts()\
                .get_or_none()

            if not metadata:
                return 'Episode not found', 404

            video_path = path_mappings.path_replace(metadata['path'])
        else:
            metadata = TableMovies.select(TableMovies.path).where(TableMovies.radarrId == id).dicts().get_or_none()

            if not metadata:
                return 'Movie not found', 404

            video_path = path_mappings.path_replace_movie(metadata['path'])

        if action == 'sync':
            subsync = SubSyncer()
            if media_type == 'episode':
                subsync.sync(video_path=video_path, srt_path=subtitles_path,
                             srt_lang=language, media_type='series', sonarr_series_id=metadata['sonarrSeriesId'],
                             sonarr_episode_id=int(id))
            else:
                subsync.sync(video_path=video_path, srt_path=subtitles_path,
                             srt_lang=language, media_type='movies', radarr_id=id)
            del subsync
            gc.collect()
        elif action == 'translate':
            from_language = subtitles_lang_from_filename(subtitles_path)
            dest_language = language
            forced = True if args.get('forced') == 'true' else False
            hi = True if args.get('hi') == 'true' else False
            translate_subtitles_file(video_path=video_path, source_srt_file=subtitles_path,
                                     from_lang=from_language, to_lang=dest_language, forced=forced, hi=hi,
                                     media_type="series" if media_type == "episode" else "movies",
                                     sonarr_series_id=metadata.get('sonarrSeriesId'),
                                     sonarr_episode_id=int(id),
                                     radarr_id=id)
        else:
            use_original_format = True if args.get('original_format') == 'true' else False
            subtitles_apply_mods(language, subtitles_path, [action], use_original_format)

        # apply chmod if required
        chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
            'win') and settings.general.getboolean('chmod_enabled') else None
        if chmod:
            os.chmod(subtitles_path, chmod)

        if media_type == 'episode':
            store_subtitles(path_mappings.path_replace_reverse(video_path), video_path)
            event_stream(type='series', payload=metadata['sonarrSeriesId'])
            event_stream(type='episode', payload=int(id))
        else:
            store_subtitles_movie(path_mappings.path_replace_reverse_movie(video_path), video_path)
            event_stream(type='movie', payload=int(id))

        return '', 204


def subtitles_lang_from_filename(path):
    split_extensionless_path = os.path.splitext(path.lower())[0].rsplit(".", 2)

    if len(split_extensionless_path) < 2:
        return None
    elif len(split_extensionless_path) == 2:
        return_lang = split_extensionless_path[-1]
    else:
        first_ext = split_extensionless_path[-1]
        second_ext = split_extensionless_path[-2]

        if first_ext in ['hi', 'sdh', 'cc']:
            if alpha3_from_alpha2(second_ext):
                return_lang = second_ext
            else:
                return first_ext
        else:
            return_lang = first_ext

    return return_lang.replace('_', '-')
