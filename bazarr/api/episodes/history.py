# coding=utf-8

import datetime
import os
import operator
import pretty

from flask_restx import Resource, Namespace, reqparse, fields
from functools import reduce
from peewee import fn
from datetime import timedelta

from app.database import get_exclusion_clause, TableEpisodes, TableShows, TableHistory, TableBlacklist
from app.config import settings
from utilities.path_mappings import path_mappings
from api.swaggerui import subtitles_language_model

from ..utils import authenticate, postprocessEpisode

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

        upgradable_episodes_not_perfect = []
        if settings.general.getboolean('upgrade_subs'):
            days_to_upgrade_subs = settings.general.days_to_upgrade_subs
            minimum_timestamp = ((datetime.datetime.now() - timedelta(days=int(days_to_upgrade_subs))) -
                                 datetime.datetime(1970, 1, 1)).total_seconds()

            if settings.general.getboolean('upgrade_manual'):
                query_actions = [1, 2, 3, 6]
            else:
                query_actions = [1, 3]

            upgradable_episodes_conditions = [(TableHistory.action.in_(query_actions)),
                                              (TableHistory.timestamp > minimum_timestamp),
                                              (TableHistory.score.is_null(False))]
            upgradable_episodes_conditions += get_exclusion_clause('series')
            upgradable_episodes = TableHistory.select(TableHistory.video_path,
                                                      fn.MAX(TableHistory.timestamp).alias('timestamp'),
                                                      TableHistory.score,
                                                      TableShows.tags,
                                                      TableEpisodes.monitored,
                                                      TableShows.seriesType) \
                .join(TableEpisodes, on=(TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId)) \
                .join(TableShows, on=(TableHistory.sonarrSeriesId == TableShows.sonarrSeriesId)) \
                .where(reduce(operator.and_, upgradable_episodes_conditions)) \
                .group_by(TableHistory.video_path,
                          TableHistory.score,
                          TableShows.tags,
                          TableEpisodes.monitored,
                          TableShows.seriesType) \
                .dicts()
            upgradable_episodes = list(upgradable_episodes)
            for upgradable_episode in upgradable_episodes:
                if upgradable_episode['timestamp'] > minimum_timestamp:
                    try:
                        int(upgradable_episode['score'])
                    except ValueError:
                        pass
                    else:
                        if int(upgradable_episode['score']) < 360:
                            upgradable_episodes_not_perfect.append(upgradable_episode)

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
            if {"video_path": str(item['path']), "timestamp": float(item['timestamp']), "score": str(item['score']),
                "tags": str(item['tags']), "monitored": str(item['monitored']),
                "seriesType": str(item['seriesType'])} in upgradable_episodes_not_perfect:  # noqa: E129
                if os.path.exists(path_mappings.path_replace(item['subtitles_path'])) and \
                        os.path.exists(path_mappings.path_replace(item['video_path'])):
                    item.update({"upgradable": True})

            del item['path']

            postprocessEpisode(item)

            if item['score']:
                item['score'] = str(round((int(item['score']) * 100 / 360), 2)) + "%"

            # Make timestamp pretty
            if item['timestamp']:
                item["raw_timestamp"] = int(item['timestamp'])
                item["parsed_timestamp"] = datetime.datetime.fromtimestamp(int(item['timestamp'])).strftime('%x %X')
                item['timestamp'] = pretty.date(item["raw_timestamp"])

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
