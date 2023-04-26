# coding=utf-8

import operator

from flask_restx import Resource, Namespace, reqparse, fields
from functools import reduce

from app.database import get_exclusion_clause, TableEpisodes, TableShows, database, select
from api.swaggerui import subtitles_language_model

from ..utils import authenticate, postprocess

api_ns_episodes_wanted = Namespace('Episodes Wanted', description='List episodes wanted subtitles')


@api_ns_episodes_wanted.route('episodes/wanted')
class EpisodesWanted(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')
    get_request_parser.add_argument('episodeid[]', type=int, action='append', required=False, default=[],
                                    help='Episodes ID to list')

    get_subtitles_language_model = api_ns_episodes_wanted.model('subtitles_language_model', subtitles_language_model)

    data_model = api_ns_episodes_wanted.model('wanted_episodes_data_model', {
        'seriesTitle': fields.String(),
        'monitored': fields.Boolean(),
        'episode_number': fields.String(),
        'episodeTitle': fields.String(),
        'missing_subtitles': fields.Nested(get_subtitles_language_model),
        'sonarrSeriesId': fields.Integer(),
        'sonarrEpisodeId': fields.Integer(),
        'sceneName': fields.String(),
        'tags': fields.List(fields.String),
        'failedAttempts': fields.String(),
        'seriesType': fields.String(),
    })

    get_response_model = api_ns_episodes_wanted.model('EpisodeWantedGetResponse', {
        'data': fields.Nested(data_model),
        'total': fields.Integer(),
    })

    @authenticate
    @api_ns_episodes_wanted.marshal_with(get_response_model, code=200)
    @api_ns_episodes_wanted.response(401, 'Not Authenticated')
    @api_ns_episodes_wanted.doc(parser=get_request_parser)
    def get(self):
        """List episodes wanted subtitles"""
        args = self.get_request_parser.parse_args()
        episodeid = args.get('episodeid[]')

        wanted_conditions = [(TableEpisodes.missing_subtitles != '[]')]
        if len(episodeid) > 0:
            wanted_conditions.append((TableEpisodes.sonarrEpisodeId in episodeid))
            start = 0
            length = 0
        else:
            start = args.get('start')
            length = args.get('length')

        wanted_conditions += get_exclusion_clause('series')
        wanted_condition = reduce(operator.and_, wanted_conditions)

        stmt = select(TableShows.title.label('seriesTitle'),
                      TableEpisodes.monitored,
                      TableEpisodes.season.concat('x').concat(TableEpisodes.episode).label('episode_number'),
                      TableEpisodes.title.label('episodeTitle'),
                      TableEpisodes.missing_subtitles,
                      TableEpisodes.sonarrSeriesId,
                      TableEpisodes.sonarrEpisodeId,
                      TableEpisodes.sceneName,
                      TableShows.tags,
                      TableEpisodes.failedAttempts,
                      TableShows.seriesType) \
            .join(TableShows, TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId) \
            .where(wanted_condition)

        if length > 0:
            stmt = stmt.order_by(TableEpisodes.sonarrEpisodeId.desc()).limit(length).offset(start)

        results = [postprocess({
            'seriesTitle': x.seriesTitle,
            'monitored': x.monitored,
            'episode_number': x.episode_number,
            'episodeTitle': x.episodeTitle,
            'missing_subtitles': x.missing_subtitles,
            'sonarrSeriesId': x.sonarrSeriesId,
            'sonarrEpisodeId': x.sonarrEpisodeId,
            'sceneName': x.sceneName,
            'tags': x.tags,
            'failedAttempts': x.failedAttempts,
            'seriesType': x.seriesType,
        }) for x in database.execute(stmt).all()]

        return {'data': results, 'total': len(results)}
