# coding=utf-8

import datetime
import os
import operator
import pretty

from flask import request, jsonify
from flask_restful import Resource
from functools import reduce
from peewee import fn
from datetime import timedelta

from database import get_exclusion_clause, TableEpisodes, TableShows, TableHistory, TableBlacklist
from ..utils import authenticate, postprocessEpisode
from config import settings
from helper import path_mappings


class EpisodesHistory(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        episodeid = request.args.get('episodeid')

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
                                              (TableHistory.score is not None)]
            upgradable_episodes_conditions += get_exclusion_clause('series')
            upgradable_episodes = TableHistory.select(TableHistory.video_path,
                                                      fn.MAX(TableHistory.timestamp).alias('timestamp'),
                                                      TableHistory.score,
                                                      TableShows.tags,
                                                      TableEpisodes.monitored,
                                                      TableShows.seriesType)\
                .join(TableEpisodes, on=(TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId))\
                .join(TableShows, on=(TableHistory.sonarrSeriesId == TableShows.sonarrSeriesId))\
                .where(reduce(operator.and_, upgradable_episodes_conditions))\
                .group_by(TableHistory.video_path)\
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

        query_conditions = [(TableEpisodes.title is not None)]
        if episodeid:
            query_conditions.append((TableEpisodes.sonarrEpisodeId == episodeid))
        query_condition = reduce(operator.and_, query_conditions)
        episode_history = TableHistory.select(TableHistory.id,
                                              TableShows.title.alias('seriesTitle'),
                                              TableEpisodes.monitored,
                                              TableEpisodes.season.concat('x').concat(TableEpisodes.episode).alias('episode_number'),
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
                                              TableHistory.subtitles_path,
                                              TableHistory.sonarrEpisodeId,
                                              TableHistory.provider,
                                              TableShows.seriesType)\
            .join(TableShows, on=(TableHistory.sonarrSeriesId == TableShows.sonarrSeriesId))\
            .join(TableEpisodes, on=(TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId))\
            .where(query_condition)\
            .order_by(TableHistory.timestamp.desc())\
            .limit(length)\
            .offset(start)\
            .dicts()
        episode_history = list(episode_history)

        blacklist_db = TableBlacklist.select(TableBlacklist.provider, TableBlacklist.subs_id).dicts()
        blacklist_db = list(blacklist_db)

        for item in episode_history:
            # Mark episode as upgradable or not
            item.update({"upgradable": False})
            if {"video_path": str(item['path']), "timestamp": float(item['timestamp']), "score": str(item['score']),
                "tags": str(item['tags']), "monitored": str(item['monitored']),
                "seriesType": str(item['seriesType'])} in upgradable_episodes_not_perfect:
                if os.path.isfile(path_mappings.path_replace(item['subtitles_path'])):
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

        count = TableHistory.select()\
            .join(TableEpisodes, on=(TableHistory.sonarrEpisodeId == TableEpisodes.sonarrEpisodeId))\
            .where(TableEpisodes.title is not None).count()

        return jsonify(data=episode_history, total=count)
