# coding=utf-8

import operator

from flask_restx import Resource, Namespace, reqparse, fields, marshal
from functools import reduce

from app.database import get_exclusion_clause, TableEpisodes, TableShows, TableMissingSubtitles, database, select, func, get_subtitles_map
from api.swaggerui import subtitles_language_model
from subtitles.wanted_state import get_missing_languages_map

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
        'episode_number': fields.String(),
        'episodeTitle': fields.String(),
        'missing_subtitles': fields.Nested(get_subtitles_language_model),
        'sonarrSeriesId': fields.Integer(),
        'sonarrEpisodeId': fields.Integer(),
        'sceneName': fields.String(),
        'tags': fields.List(fields.String),
        'seriesType': fields.String(),
    })

    get_response_model = api_ns_episodes_wanted.model('EpisodeWantedGetResponse', {
        'data': fields.Nested(data_model),
        'total': fields.Integer(),
    })

    @authenticate
    @api_ns_episodes_wanted.response(401, 'Not Authenticated')
    @api_ns_episodes_wanted.doc(parser=get_request_parser)
    def get(self):
        """List episodes wanted subtitles"""
        args = self.get_request_parser.parse_args()
        episodeid = args.get('episodeid[]')

        wanted_conditions = [select(TableMissingSubtitles.id)
                             .where(TableMissingSubtitles.media_type == 'series')
                             .where(TableMissingSubtitles.media_id == TableEpisodes.sonarrEpisodeId)
                             .exists()]
        if len(episodeid) > 0:
            wanted_conditions.append((TableEpisodes.sonarrEpisodeId.in_(episodeid)))
            start = 0
            length = 0
        else:
            start = args.get('start')
            length = args.get('length')

        wanted_conditions += get_exclusion_clause('series')
        wanted_condition = reduce(operator.and_, wanted_conditions)

        stmt = select(TableShows.title.label('seriesTitle'),
                      TableEpisodes.season.concat('x').concat(TableEpisodes.episode).label('episode_number'),
                      TableEpisodes.title.label('episodeTitle'),
                      TableEpisodes.sonarrSeriesId,
                      TableEpisodes.sonarrEpisodeId,
                      TableEpisodes.sceneName,
                      TableShows.tags,
                      TableShows.seriesType) \
            .select_from(TableEpisodes) \
            .join(TableShows) \
            .where(wanted_condition)

        if length > 0:
            stmt = stmt.order_by(TableEpisodes.sonarrEpisodeId.desc()).limit(length).offset(start)

        episodes = database.execute(stmt).all()
        missing_languages = get_missing_languages_map('series', [x.sonarrEpisodeId for x in episodes])
        subtitles_map = get_subtitles_map('series', [x.sonarrEpisodeId for x in episodes])

        results = [postprocess({
            'seriesTitle': x.seriesTitle,
            'episode_number': x.episode_number,
            'episodeTitle': x.episodeTitle,
            'missing_subtitles': missing_languages[x.sonarrEpisodeId],
            'sonarrSeriesId': x.sonarrSeriesId,
            'sonarrEpisodeId': x.sonarrEpisodeId,
            'sceneName': x.sceneName,
            'tags': x.tags,
            'seriesType': x.seriesType,
        }, subtitles=subtitles_map.get(x.sonarrEpisodeId, [])) for x in episodes]

        count = database.execute(
            select(func.count())
            .select_from(TableEpisodes)
            .join(TableShows)
            .where(wanted_condition)) \
            .scalar()

        return marshal({'data': results, 'total': count}, self.get_response_model)
