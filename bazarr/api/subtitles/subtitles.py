# coding=utf-8

import os
import sys
import gc

from flask_restx import Resource, Namespace, reqparse, fields, marshal

from app.database import TableEpisodes, TableMovies, database, select
from languages.get_languages import alpha3_from_alpha2
from utilities.path_mappings import path_mappings
from utilities.video_analyzer import subtitles_sync_references
from subtitles.tools.subsyncer import SubSyncer
from subtitles.tools.translate.main import translate_subtitles_file
from subtitles.tools.mods import subtitles_apply_mods
from subtitles.indexer.series import store_subtitles
from subtitles.indexer.movies import store_subtitles_movie
from app.config import settings, empty_values, get_array_from
from app.event_handler import event_stream

from ..utils import authenticate

api_ns_subtitles = Namespace('Subtitles', description='Apply mods/tools on external subtitles')


@api_ns_subtitles.route('subtitles')
class Subtitles(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('subtitlesPath', type=str, required=True, help='External subtitles file path')
    get_request_parser.add_argument('sonarrEpisodeId', type=int, required=False, help='Sonarr Episode ID')
    get_request_parser.add_argument('radarrMovieId', type=int, required=False, help='Radarr Movie ID')

    audio_tracks_data_model = api_ns_subtitles.model('audio_tracks_data_model', {
        'stream': fields.String(),
        'name': fields.String(),
        'language': fields.String(),
    })

    embedded_subtitles_data_model = api_ns_subtitles.model('embedded_subtitles_data_model', {
        'stream': fields.String(),
        'name': fields.String(),
        'language': fields.String(),
        'forced': fields.Boolean(),
        'hearing_impaired': fields.Boolean(),
    })

    external_subtitles_data_model = api_ns_subtitles.model('external_subtitles_data_model', {
        'name': fields.String(),
        'path': fields.String(),
        'language': fields.String(),
        'forced': fields.Boolean(),
        'hearing_impaired': fields.Boolean(),
    })

    get_response_model = api_ns_subtitles.model('SubtitlesGetResponse', {
        'audio_tracks': fields.Nested(audio_tracks_data_model),
        'embedded_subtitles_tracks': fields.Nested(embedded_subtitles_data_model),
        'external_subtitles_tracks': fields.Nested(external_subtitles_data_model),
    })

    @authenticate
    @api_ns_subtitles.response(200, 'Success')
    @api_ns_subtitles.response(401, 'Not Authenticated')
    @api_ns_subtitles.doc(parser=get_request_parser)
    def get(self):
        """Return available audio and embedded subtitles tracks with external subtitles. Used for manual subsync
        modal"""
        args = self.get_request_parser.parse_args()
        subtitlesPath = args.get('subtitlesPath')
        episodeId = args.get('sonarrEpisodeId', None)
        movieId = args.get('radarrMovieId', None)

        result = subtitles_sync_references(subtitles_path=subtitlesPath, sonarr_episode_id=episodeId,
                                           radarr_movie_id=movieId)

        return marshal(result, self.get_response_model, envelope='data')

    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('action', type=str, required=True,
                                      help='Action from ["sync", "translate" or mods name]')
    patch_request_parser.add_argument('language', type=str, required=True, help='Language code2')
    patch_request_parser.add_argument('path', type=str, required=True, help='Subtitles file path')
    patch_request_parser.add_argument('type', type=str, required=True, help='Media type from ["episode", "movie"]')
    patch_request_parser.add_argument('id', type=int, required=True, help='Media ID (episodeId, radarrId)')
    patch_request_parser.add_argument('forced', type=str, required=False,
                                      help='Forced subtitles from ["True", "False"]')
    patch_request_parser.add_argument('hi', type=str, required=False, help='HI subtitles from ["True", "False"]')
    patch_request_parser.add_argument('original_format', type=str, required=False,
                                      help='Use original subtitles format from ["True", "False"]')
    patch_request_parser.add_argument('reference', type=str, required=False,
                                      help='Reference to use for sync from video file track number (a:0) or some '
                                           'subtitles file path')
    patch_request_parser.add_argument('max_offset_seconds', type=str, required=False,
                                      help='Maximum offset seconds to allow')
    patch_request_parser.add_argument('no_fix_framerate', type=str, required=False,
                                      help='Don\'t try to fix framerate from ["True", "False"]')
    patch_request_parser.add_argument('gss', type=str, required=False,
                                      help='Use Golden-Section Search from ["True", "False"]')

    @authenticate
    @api_ns_subtitles.doc(parser=patch_request_parser)
    @api_ns_subtitles.response(204, 'Success')
    @api_ns_subtitles.response(401, 'Not Authenticated')
    @api_ns_subtitles.response(404, 'Episode/movie not found')
    @api_ns_subtitles.response(409, 'Unable to edit subtitles file. Check logs.')
    @api_ns_subtitles.response(500, 'Subtitles file not found. Path mapping issue?')
    def patch(self):
        """Apply mods/tools on external subtitles"""
        args = self.patch_request_parser.parse_args()
        action = args.get('action')

        language = args.get('language')
        subtitles_path = args.get('path')
        media_type = args.get('type')
        id = args.get('id')
        forced = True if args.get('forced') == 'True' else False
        hi = True if args.get('hi') == 'True' else False

        if not os.path.exists(subtitles_path):
            return 'Subtitles file not found. Path mapping issue?', 500

        if media_type == 'episode':
            metadata = database.execute(
                select(TableEpisodes.path, TableEpisodes.sonarrSeriesId, TableEpisodes.subtitles)
                .where(TableEpisodes.sonarrEpisodeId == id)) \
                .first()

            if not metadata:
                return 'Episode not found', 404

            video_path = path_mappings.path_replace(metadata.path)
        else:
            metadata = database.execute(
                select(TableMovies.path, TableMovies.subtitles)
                .where(TableMovies.radarrId == id))\
                .first()

            if not metadata:
                return 'Movie not found', 404

            video_path = path_mappings.path_replace_movie(metadata.path)

        if action == 'sync':
            sync_kwargs = {
                'video_path': video_path,
                'srt_path': subtitles_path,
                'srt_lang': language,
                'hi': hi,
                'forced': forced,
                'reference': args.get('reference') if args.get('reference') not in empty_values else video_path,
                'max_offset_seconds': args.get('max_offset_seconds') if args.get('max_offset_seconds') not in
                empty_values else str(settings.subsync.max_offset_seconds),
                'no_fix_framerate': args.get('no_fix_framerate') == 'True',
                'gss': args.get('gss') == 'True',
            }

            subsync = SubSyncer()
            try:
                if media_type == 'episode':
                    sync_kwargs['sonarr_series_id'] = metadata.sonarrSeriesId
                    sync_kwargs['sonarr_episode_id'] = id
                else:
                    sync_kwargs['radarr_id'] = id
                subsync.sync(**sync_kwargs)
            except OSError:
                return 'Unable to edit subtitles file. Check logs.', 409
            finally:
                del subsync
                gc.collect()
        elif action == 'translate':
            dest_language = language
            from_language = None

            if metadata.subtitles:
                subtitles_list = get_array_from(metadata.subtitles)
                subtitles_filename = os.path.basename(subtitles_path)

                for subtitle_entry in subtitles_list:
                    if len(subtitle_entry) >= 2 and subtitle_entry[1] is not None:
                        db_subtitle_filename = os.path.basename(subtitle_entry[1])
                        if db_subtitle_filename == subtitles_filename:
                            from_language = subtitle_entry[0]
                            break

                if not from_language or not alpha3_from_alpha2(from_language):
                    from_language = subtitles_lang_from_filename(subtitles_path)
                if not from_language or not alpha3_from_alpha2(from_language):
                    return 'Invalid source language code', 400

                try:
                    translate_subtitles_file(video_path=video_path, source_srt_file=subtitles_path,
                                             from_lang=from_language, to_lang=dest_language, forced=forced, hi=hi,
                                             media_type="series" if media_type == "episode" else "movies",
                                             sonarr_series_id=metadata.sonarrSeriesId if media_type == "episode" else None,
                                             sonarr_episode_id=id,
                                             radarr_id=id)
                except OSError:
                    return 'Unable to edit subtitles file. Check logs.', 409
        else:
            use_original_format = True if args.get('original_format') == 'true' else False
            try:
                subtitles_apply_mods(language=language, subtitle_path=subtitles_path, mods=[action],
                                     use_original_format=use_original_format, video_path=video_path)
            except OSError:
                return 'Unable to edit subtitles file. Check logs.', 409

        # apply chmod if required
        chmod = int(settings.general.chmod, 8) if not sys.platform.startswith(
            'win') and settings.general.chmod_enabled else None
        if chmod:
            os.chmod(subtitles_path, chmod)

        if media_type == 'episode':
            store_subtitles(path_mappings.path_replace_reverse(video_path), video_path)
            event_stream(type='series', payload=metadata.sonarrSeriesId)
            event_stream(type='episode', payload=id)
        else:
            store_subtitles_movie(path_mappings.path_replace_reverse_movie(video_path), video_path)
            event_stream(type='movie', payload=id)

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
