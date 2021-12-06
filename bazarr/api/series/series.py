# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

import operator
from functools import reduce

from database import get_exclusion_clause, TableEpisodes, TableShows
from list_subtitles import list_missing_subtitles, series_scan_subtitles
from get_subtitle import series_download_subtitles, wanted_search_missing_subtitles_series
from ..utils import authenticate, postprocessSeries, None_Keys
from event_handler import event_stream


class Series(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        seriesId = request.args.getlist('seriesid[]')

        count = TableShows.select().count()

        if len(seriesId) != 0:
            result = TableShows.select() \
                .where(TableShows.seriesId.in_(seriesId)) \
                .order_by(TableShows.sortTitle).dicts()
        else:
            result = TableShows.select().order_by(TableShows.sortTitle).limit(length).offset(start).dicts()

        result = list(result)

        for item in result:
            postprocessSeries(item)

            # Add missing subtitles episode count
            episodes_missing_conditions = [(TableEpisodes.seriesId == item['seriesId']),
                                           (TableEpisodes.missing_subtitles != '[]')]
            episodes_missing_conditions += get_exclusion_clause('series')

            episodeMissingCount = TableEpisodes.select(TableShows.tags,
                                                       TableEpisodes.monitored,
                                                       TableShows.seriesType) \
                .join(TableShows) \
                .where(reduce(operator.and_, episodes_missing_conditions)) \
                .count()
            item.update({"episodeMissingCount": episodeMissingCount})

            # Add episode count
            episodeFileCount = TableEpisodes.select(TableShows.tags,
                                                    TableEpisodes.monitored,
                                                    TableShows.seriesType) \
                .join(TableShows) \
                .where(TableEpisodes.seriesId == item['seriesId']) \
                .count()
            item.update({"episodeFileCount": episodeFileCount})

        return jsonify(data=result, total=count)

    @authenticate
    def post(self):
        seriesIdList = request.form.getlist('seriesid')
        profileIdList = request.form.getlist('profileid')
        monitoredList = request.form.getlist('monitored')

        for idx in range(len(seriesIdList)):
            seriesId = seriesIdList[idx]
            profileId = profileIdList[idx]
            monitored = monitoredList[idx]

            if profileId in None_Keys:
                profileId = None
            else:
                try:
                    profileId = int(profileId)
                except Exception:
                    return '', 400

            TableShows.update({
                TableShows.profileId: profileId,
                TableShows.monitored: monitored
            }) \
                .where(TableShows.seriesId == seriesId) \
                .execute()

            TableEpisodes.update({
                TableEpisodes.monitored: monitored
            }) \
                .where(TableEpisodes.seriesId == seriesId) \
                .execute()

            list_missing_subtitles(no=seriesId, send_event=False)

            event_stream(type='series', payload=seriesId)

            episode_id_list = TableEpisodes \
                .select(TableEpisodes.episodeId) \
                .where(TableEpisodes.seriesId == seriesId) \
                .dicts()

            for item in episode_id_list:
                event_stream(type='episode', payload=item['episodeId'])
                event_stream(type='episode-wanted', payload=item['episodeId'])

        event_stream(type='badges')

        return '', 204

    @authenticate
    def patch(self):
        seriesid = request.form.get('seriesid')
        action = request.form.get('action')
        value = request.form.get('value')
        tmdbid = request.form.get('tmdbid')

        if tmdbid:
            TableShows.update({TableShows.tmdbId: tmdbid}).where(TableShows.seriesId == seriesid).execute()
            event_stream(type='series', payload=seriesid)
            series_scan_subtitles(seriesid)
            return '', 204
        elif action == "refresh":
            series_scan_subtitles(seriesid)
            return '', 204
        elif action == "search-missing":
            series_download_subtitles(seriesid)
            return '', 204
        elif action == "search-wanted":
            wanted_search_missing_subtitles_series()
            return '', 204
        elif action == "monitored":
            if value == 'false':
                new_monitored_value = 'True'
            else:
                new_monitored_value = 'False'

            # update series monitored status
            TableShows.update({
                TableShows.monitored: new_monitored_value
            }) \
                .where(TableShows.seriesId == seriesid) \
                .execute()

            event_stream(type='series', payload=seriesid)

            # update each series episode monitored status
            series_episodes = TableEpisodes.select(TableEpisodes.episodeId) \
                .where(TableEpisodes.seriesId == seriesid) \
                .dicts()

            TableEpisodes.update({
                TableEpisodes.monitored: new_monitored_value
            }) \
                .where(TableEpisodes.seriesId == seriesid) \
                .execute()

            for episodeid in series_episodes:
                event_stream(type='badges')
                event_stream(type='episode-wanted', payload=episodeid['episodeId'])

            return '', 204

        return '', 400
