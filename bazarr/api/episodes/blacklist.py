# coding=utf-8

import datetime
import pretty

from flask_restx import Resource, Namespace, reqparse, fields

from app.database import TableEpisodes, TableShows, TableBlacklist
from subtitles.tools.delete import delete_subtitles
from sonarr.blacklist import blacklist_log, blacklist_delete_all, blacklist_delete
from utilities.path_mappings import path_mappings
from subtitles.mass_download import episode_download_subtitles
from app.event_handler import event_stream
from api.swaggerui import subtitles_language_model

from ..utils import authenticate, postprocessEpisode

api_ns_episodes_blacklist = Namespace('Episodes Blacklist', description='List, add or remove subtitles to or from '
                                                                        'episodes blacklist')


@api_ns_episodes_blacklist.route('episodes/blacklist')
class EpisodesBlacklist(Resource):
    # GET: get blacklist
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')

    get_language_model = api_ns_episodes_blacklist.model('language_model', subtitles_language_model)

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
    @api_ns_episodes_blacklist.marshal_with(get_response_model, envelope='data', code=200)
    @api_ns_episodes_blacklist.doc(parser=get_request_parser)
    def get(self):
        args = self.get_request_parser.parse_args()
        start = args.get('start')
        length = args.get('length')

        data = TableBlacklist.select(TableShows.title.alias('seriesTitle'),
                                     TableEpisodes.season.concat('x').concat(TableEpisodes.episode).alias('episode_number'),
                                     TableEpisodes.title.alias('episodeTitle'),
                                     TableEpisodes.sonarrSeriesId,
                                     TableBlacklist.provider,
                                     TableBlacklist.subs_id,
                                     TableBlacklist.language,
                                     TableBlacklist.timestamp)\
            .join(TableEpisodes, on=(TableBlacklist.sonarr_episode_id == TableEpisodes.sonarrEpisodeId))\
            .join(TableShows, on=(TableBlacklist.sonarr_series_id == TableShows.sonarrSeriesId))\
            .order_by(TableBlacklist.timestamp.desc())\
            .limit(length)\
            .offset(start)\
            .dicts()
        data = list(data)

        for item in data:
            # Make timestamp pretty
            item["parsed_timestamp"] = datetime.datetime.fromtimestamp(int(item['timestamp'])).strftime('%x %X')
            item.update({'timestamp': pretty.date(datetime.datetime.fromtimestamp(item['timestamp']))})

            postprocessEpisode(item)

        return data

    # POST: add blacklist
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
    @api_ns_episodes_blacklist.response(404, 'Episode not found')
    def post(self):
        args = self.post_request_parser.parse_args()
        sonarr_series_id = args.get('seriesid')
        sonarr_episode_id = args.get('episodeid')
        provider = args.get('provider')
        subs_id = args.get('subs_id')
        language = args.get('language')

        episodeInfo = TableEpisodes.select(TableEpisodes.path)\
            .where(TableEpisodes.sonarrEpisodeId == sonarr_episode_id)\
            .dicts()\
            .get_or_none()

        if not episodeInfo:
            return 'Episode not found', 404

        media_path = episodeInfo['path']
        subtitles_path = args.get('subtitles_path')

        blacklist_log(sonarr_series_id=sonarr_series_id,
                      sonarr_episode_id=sonarr_episode_id,
                      provider=provider,
                      subs_id=subs_id,
                      language=language)
        delete_subtitles(media_type='series',
                         language=language,
                         forced=False,
                         hi=False,
                         media_path=path_mappings.path_replace(media_path),
                         subtitles_path=subtitles_path,
                         sonarr_series_id=sonarr_series_id,
                         sonarr_episode_id=sonarr_episode_id)
        episode_download_subtitles(sonarr_episode_id)
        event_stream(type='episode-history')
        return '', 200

    # DELETE: remove blacklist
    delete_request_parser = reqparse.RequestParser()
    delete_request_parser.add_argument('all', type=str, required=False, help='Empty episodes subtitles blacklist')
    delete_request_parser.add_argument('provider', type=str, required=True, help='Provider name')
    delete_request_parser.add_argument('subs_id', type=str, required=True, help='Subtitles ID')

    @authenticate
    @api_ns_episodes_blacklist.doc(parser=delete_request_parser)
    @api_ns_episodes_blacklist.response(204, 'Success')
    def delete(self):
        args = self.post_request_parser.parse_args()

        if args.get("all") == "true":
            blacklist_delete_all()
        else:
            provider = args.get('provider')
            subs_id = args.get('subs_id')
            blacklist_delete(provider=provider, subs_id=subs_id)
        return '', 204
