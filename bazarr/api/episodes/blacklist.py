# coding=utf-8

import datetime
import pretty

from flask import request, jsonify
from flask_restful import Resource

from database import TableEpisodes, TableShows, TableBlacklist
from ..utils import authenticate, postprocessEpisode
from utils import blacklist_log, delete_subtitles, blacklist_delete_all, blacklist_delete
from helper import path_mappings
from get_subtitle.mass_download import episode_download_subtitles
from event_handler import event_stream


# GET: get blacklist
# POST: add blacklist
# DELETE: remove blacklist
class EpisodesBlacklist(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1

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

        return jsonify(data=data)

    @authenticate
    def post(self):
        sonarr_series_id = int(request.args.get('seriesid'))
        sonarr_episode_id = int(request.args.get('episodeid'))
        provider = request.form.get('provider')
        subs_id = request.form.get('subs_id')
        language = request.form.get('language')

        episodeInfo = TableEpisodes.select(TableEpisodes.path)\
            .where(TableEpisodes.sonarrEpisodeId == sonarr_episode_id)\
            .dicts()\
            .get()

        media_path = episodeInfo['path']
        subtitles_path = request.form.get('subtitles_path')

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

    @authenticate
    def delete(self):
        if request.args.get("all") == "true":
            blacklist_delete_all()
        else:
            provider = request.form.get('provider')
            subs_id = request.form.get('subs_id')
            blacklist_delete(provider=provider, subs_id=subs_id)
        return '', 204
