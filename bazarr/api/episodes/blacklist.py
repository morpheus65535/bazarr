# coding=utf-8

import pretty

from flask_restx import Resource, Namespace, reqparse, fields, marshal

from app.database import TableEpisodes, TableShows, TableBlacklist, database, select
from subtitles.tools.delete import delete_subtitles
from sonarr.blacklist import blacklist_log, blacklist_delete_all, blacklist_delete
from utilities.path_mappings import path_mappings
from subtitles.mass_download import episode_download_subtitles
from app.event_handler import event_stream
from api.swaggerui import subtitles_language_model

from ..utils import authenticate, postprocess

api_ns_episodes_blacklist = Namespace('Episodes Blacklist', description='List, add or remove subtitles to or from '
                                                                        'episodes blacklist')


@api_ns_episodes_blacklist.route('episodes/blacklist')
class EpisodesBlacklist(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')

    get_language_model = api_ns_episodes_blacklist.model('subtitles_language_model', subtitles_language_model)

    get_response_model = api_ns_episodes_blacklist.model('EpisodeBlacklistGetResponse', {
        'seriesTitle': fields.String(),
        'episode_number': fields.String(),
        'episodeTitle': fields.String(),
        'sonarrSeriesId': fields.Integer(),
        'provider': fields.String(),
        'subs_id': fields.String(),
        'language': fields.Nested(get_language_model),
        'timestamp': fields.String(),
        'parsed_timestamp': fields.String(),
    })

    @authenticate
    @api_ns_episodes_blacklist.response(401, 'Not Authenticated')
    @api_ns_episodes_blacklist.doc(parser=get_request_parser)
    def get(self):
        """List blacklisted episodes subtitles"""
        args = self.get_request_parser.parse_args()
        start = args.get('start')
        length = args.get('length')

        stmt = select(TableShows.title.label('seriesTitle'),
                      TableEpisodes.season.concat('x').concat(TableEpisodes.episode).label('episode_number'),
                      TableEpisodes.title.label('episodeTitle'),
                      TableEpisodes.sonarrSeriesId,
                      TableBlacklist.provider,
                      TableBlacklist.subs_id,
                      TableBlacklist.language,
                      TableBlacklist.timestamp) \
            .select_from(TableBlacklist) \
            .join(TableShows, onclause=TableBlacklist.sonarr_series_id == TableShows.sonarrSeriesId) \
            .join(TableEpisodes, onclause=TableBlacklist.sonarr_episode_id == TableEpisodes.sonarrEpisodeId) \
            .order_by(TableBlacklist.timestamp.desc())
        if length > 0:
            stmt = stmt.limit(length).offset(start)

        return marshal([postprocess({
            'seriesTitle': x.seriesTitle,
            'episode_number': x.episode_number,
            'episodeTitle': x.episodeTitle,
            'sonarrSeriesId': x.sonarrSeriesId,
            'provider': x.provider,
            'subs_id': x.subs_id,
            'language': x.language,
            'timestamp': pretty.date(x.timestamp),
            'parsed_timestamp': x.timestamp.strftime('%x %X')
        }) for x in database.execute(stmt).all()], self.get_response_model, envelope='data')

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('seriesid', type=int, required=True, help='Series ID')
    post_request_parser.add_argument('episodeid', type=int, required=True, help='Episode ID')
    post_request_parser.add_argument('provider', type=str, required=True, help='Provider name')
    post_request_parser.add_argument('subs_id', type=str, required=True, help='Subtitles ID')
    post_request_parser.add_argument('language', type=str, required=True, help='Subtitles language')
    post_request_parser.add_argument('subtitles_path', type=str, required=True, help='Subtitles file path')

    @authenticate
    @api_ns_episodes_blacklist.doc(parser=post_request_parser)
    @api_ns_episodes_blacklist.response(200, 'Success')
    @api_ns_episodes_blacklist.response(401, 'Not Authenticated')
    @api_ns_episodes_blacklist.response(404, 'Episode not found')
    @api_ns_episodes_blacklist.response(500, 'Subtitles file not found or permission issue.')
    def post(self):
        """Add an episodes subtitles to blacklist"""
        args = self.post_request_parser.parse_args()
        sonarr_series_id = args.get('seriesid')
        sonarr_episode_id = args.get('episodeid')
        provider = args.get('provider')
        subs_id = args.get('subs_id')
        language = args.get('language')

        episodeInfo = database.execute(
            select(TableEpisodes.path)
            .where(TableEpisodes.sonarrEpisodeId == sonarr_episode_id)) \
            .first()

        if not episodeInfo:
            return 'Episode not found', 404

        media_path = episodeInfo.path
        subtitles_path = args.get('subtitles_path')

        blacklist_log(sonarr_series_id=sonarr_series_id,
                      sonarr_episode_id=sonarr_episode_id,
                      provider=provider,
                      subs_id=subs_id,
                      language=language)
        if delete_subtitles(media_type='series',
                            language=language,
                            forced=False,
                            hi=False,
                            media_path=path_mappings.path_replace(media_path),
                            subtitles_path=subtitles_path,
                            sonarr_series_id=sonarr_series_id,
                            sonarr_episode_id=sonarr_episode_id):
            episode_download_subtitles(no=sonarr_episode_id)
            event_stream(type='episode-history')
            return '', 200
        else:
            return 'Subtitles file not found or permission issue.', 500

    delete_request_parser = reqparse.RequestParser()
    delete_request_parser.add_argument('all', type=str, required=False, help='Empty episodes subtitles blacklist')
    delete_request_parser.add_argument('provider', type=str, required=False, help='Provider name')
    delete_request_parser.add_argument('subs_id', type=str, required=False, help='Subtitles ID')

    @authenticate
    @api_ns_episodes_blacklist.doc(parser=delete_request_parser)
    @api_ns_episodes_blacklist.response(204, 'Success')
    @api_ns_episodes_blacklist.response(401, 'Not Authenticated')
    def delete(self):
        """Delete an episodes subtitles from blacklist"""
        args = self.delete_request_parser.parse_args()
        if args.get("all") == "true":
            blacklist_delete_all()
        else:
            provider = args.get('provider')
            subs_id = args.get('subs_id')
            blacklist_delete(provider=provider, subs_id=subs_id)
        return '', 204
