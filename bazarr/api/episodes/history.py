# coding=utf-8

import os
import operator
import pretty

from flask_restx import Resource, Namespace, reqparse, fields
from functools import reduce

from app.database import TableEpisodes, TableShows, TableHistory, TableBlacklist
from subtitles.upgrade import get_upgradable_episode_subtitles
from utilities.path_mappings import path_mappings
from api.swaggerui import subtitles_language_model

from ..utils import authenticate, postprocess

api_ns_episodes_history = Namespace('Episodes History', description='List episodes history events')


@api_ns_episodes_history.route('episodes/history')
class EpisodesHistory(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('start', type=int, required=False, default=0, help='Paging start integer')
    get_request_parser.add_argument('length', type=int, required=False, default=-1, help='Paging length integer')
    get_request_parser.add_argument('episodeid', type=int, required=False, help='Episode ID')

    get_language_model = api_ns_episodes_history.model('subtitles_language_model', subtitles_language_model)

    data_model = api_ns_episodes_history.model('history_episodes_data_model', {
        'id': fields.Integer(),
        'seriesTitle': fields.String(),
        'monitored': fields.Boolean(),
        'episode_number': fields.String(),
        'episodeTitle': fields.String(),
        'timestamp': fields.String(),
        'subs_id': fields.String(),
        'description': fields.String(),
        'sonarrSeriesId': fields.Integer(),
        'language': fields.Nested(get_language_model),
        'score': fields.String(),
        'tags': fields.List(fields.String),
        'action': fields.Integer(),
        'video_path': fields.String(),
        'subtitles_path': fields.String(),
        'sonarrEpisodeId': fields.Integer(),
        'provider': fields.String(),
        'seriesType': fields.String(),
        'upgradable': fields.Boolean(),
        'raw_timestamp': fields.Integer(),
        'parsed_timestamp': fields.String(),
        'blacklisted': fields.Boolean(),
    })

    get_response_model = api_ns_episodes_history.model('EpisodeHistoryGetResponse', {
        'data': fields.Nested(data_model),
        'total': fields.Integer(),
    })

    @authenticate
    @api_ns_episodes_history.marshal_with(get_response_model, code=200)
    @api_ns_episodes_history.response(401, 'Not Authenticated')
    @api_ns_episodes_history.doc(parser=get_request_parser)
    def get(self):
        """List episodes history events"""
        args = self.get_request_parser.parse_args()
        start = args.get('start')
        length = args.get('length')
        episodeid = args.get('episodeid')

        upgradable_episodes_not_perfect = get_upgradable_episode_subtitles()
        if len(upgradable_episodes_not_perfect):
            upgradable_episodes_not_perfect = [{"video_path": x['video_path'],
                                                "timestamp": x['timestamp'],
                                                "score": x['score'],
                                                "tags": x['tags'],
                                                "monitored": x['monitored'],
                                                "seriesType": x['seriesType']}
                                               for x in upgradable_episodes_not_perfect]

        query_conditions = [(TableEpisodes.title.is_null(False))]
        if episodeid:
            query_conditions.append((TableEpisodes.sonarrEpisodeId == episodeid))
        query_condition = reduce(operator.and_, query_conditions)
        episode_history = TableHistory.select(TableHistory.id,
                                              TableShows.title.alias('seriesTitle'),
                                              TableEpisodes.monitored,
                                              TableEpisodes.season.concat('x').concat(TableEpisodes.episode).alias(
                                                  'episode_number'),
                                              TableEpisodes.title.alias('episodeTitle'),
                                              TableHistory.timestamp,
                                              TableHistory.subs_id,
                                              TableHistory.description,
                                              TableHistory.sonarrSeriesId,
                                              TableEpisodes.path,
                                              TableHistory.language,
                                              TableHistory.score,
                                              TableShows.tags,
                                              TableHistory.action,
                                              TableHistory.video_path,
                                              TableHistory.subtitles_path,
                                              TableHistory.sonarrEpisodeId,
                                              TableHistory.provider,
                                              TableShows.seriesType) \
            .join(TableShows, on=(TableHistory.sonarrSeriesId == TableShows.sonarrSeriesId)) \
            .join(TableEpisodes, on=(TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId)) \
            .where(query_condition) \
            .order_by(TableHistory.timestamp.desc())
        if length > 0:
            episode_history = episode_history.limit(length).offset(start)
        episode_history = list(episode_history.dicts())

        blacklist_db = TableBlacklist.select(TableBlacklist.provider, TableBlacklist.subs_id).dicts()
        blacklist_db = list(blacklist_db)

        for item in episode_history:
            # Mark episode as upgradable or not
            item.update({"upgradable": False})
            if {"video_path": str(item['path']), "timestamp": item['timestamp'], "score": item['score'],
                "tags": str(item['tags']), "monitored": str(item['monitored']),
                "seriesType": str(item['seriesType'])} in upgradable_episodes_not_perfect:  # noqa: E129
                if os.path.exists(path_mappings.path_replace(item['subtitles_path'])) and \
                        os.path.exists(path_mappings.path_replace(item['video_path'])):
                    item.update({"upgradable": True})

            del item['path']

            postprocess(item)

            if item['score']:
                item['score'] = str(round((int(item['score']) * 100 / 360), 2)) + "%"

            # Make timestamp pretty
            if item['timestamp']:
                item["raw_timestamp"] = item['timestamp'].timestamp()
                item["parsed_timestamp"] = item['timestamp'].strftime('%x %X')
                item['timestamp'] = pretty.date(item["timestamp"])

            # Check if subtitles is blacklisted
            item.update({"blacklisted": False})
            if item['action'] not in [0, 4, 5]:
                for blacklisted_item in blacklist_db:
                    if blacklisted_item['provider'] == item['provider'] and \
                            blacklisted_item['subs_id'] == item['subs_id']:
                        item.update({"blacklisted": True})
                        break

        count = TableHistory.select() \
            .join(TableEpisodes, on=(TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId)) \
            .where(TableEpisodes.title.is_null(False)).count()

        return {'data': episode_history, 'total': count}
