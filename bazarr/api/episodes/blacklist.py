# coding=utf-8

import datetime
import pretty

from flask import request, jsonify
from flask_restx import Resource, Namespace, reqparse, fields

from app.database import TableEpisodes, TableShows, TableBlacklist
from subtitles.tools.delete import delete_subtitles
from sonarr.blacklist import blacklist_log, blacklist_delete_all, blacklist_delete
from utilities.path_mappings import path_mappings
from subtitles.mass_download import episode_download_subtitles
from app.event_handler import event_stream

from ..utils import authenticate, postprocessEpisode

api_ns_episodes_blacklist = Namespace('episodesBlacklist', description='Episodes blacklist API endpoint')


# GET: get blacklist
# POST: add blacklist
# DELETE: remove blacklist
@api_ns_episodes_blacklist.route('episodes/blacklist')
class EpisodesBlacklist(Resource):
    blacklist_get_parser = reqparse.RequestParser()
    blacklist_get_parser.add_argument('start', type=int, required=False, help='Paging start integer')
    blacklist_get_parser.add_argument('length', type=int, required=False, help='Paging length integer')

    blacklist_get_model = api_ns_episodes_blacklist.model('BlacklistGet', {
        'seriesTitle': fields.String(required=True),
        'episode_number': fields.Integer(min=0, required=True),
        'episodeTitle': fields.String(required=True),
        'sonarrSeriesId': fields.Integer(min=0, required=True),
        'provider': fields.String(required=True),
        'subs_id': fields.String(required=True),
        'language': fields.String(required=True),
        'timestamp': fields.Integer(min=0, required=True),
        'parsed_timestamp': fields.String(required=True),
    })

    @authenticate
    @api_ns_episodes_blacklist.marshal_with(blacklist_get_model)
    @api_ns_episodes_blacklist.doc(parser=blacklist_get_parser, enveloppe='data')
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

        return data

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
            .get_or_none()

        if not episodeInfo:
            return 'Episode not found', 404

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
