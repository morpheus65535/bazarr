# coding=utf-8

import datetime
import pretty

from flask import request, jsonify
from flask_restful import Resource

from database import TableMovies, TableBlacklistMovie
from ..utils import authenticate, postprocessMovie
from utils import blacklist_log_movie, delete_subtitles, blacklist_delete_all_movie, blacklist_delete_movie
from helper import path_mappings
from get_subtitle.mass_download import movies_download_subtitles
from event_handler import event_stream


# GET: get blacklist
# POST: add blacklist
# DELETE: remove blacklist
class MoviesBlacklist(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1

        data = TableBlacklistMovie.select(TableMovies.title,
                                          TableMovies.radarrId,
                                          TableBlacklistMovie.provider,
                                          TableBlacklistMovie.subs_id,
                                          TableBlacklistMovie.language,
                                          TableBlacklistMovie.timestamp)\
            .join(TableMovies, on=(TableBlacklistMovie.radarr_id == TableMovies.radarrId))\
            .order_by(TableBlacklistMovie.timestamp.desc())\
            .limit(length)\
            .offset(start)\
            .dicts()
        data = list(data)

        for item in data:
            postprocessMovie(item)

            # Make timestamp pretty
            item["parsed_timestamp"] = datetime.datetime.fromtimestamp(int(item['timestamp'])).strftime('%x %X')
            item.update({'timestamp': pretty.date(datetime.datetime.fromtimestamp(item['timestamp']))})

        return jsonify(data=data)

    @authenticate
    def post(self):
        radarr_id = int(request.args.get('radarrid'))
        provider = request.form.get('provider')
        subs_id = request.form.get('subs_id')
        language = request.form.get('language')
        # TODO
        forced = False
        hi = False

        data = TableMovies.select(TableMovies.path).where(TableMovies.radarrId == radarr_id).dicts().get()

        media_path = data['path']
        subtitles_path = request.form.get('subtitles_path')

        blacklist_log_movie(radarr_id=radarr_id,
                            provider=provider,
                            subs_id=subs_id,
                            language=language)
        delete_subtitles(media_type='movie',
                         language=language,
                         forced=forced,
                         hi=hi,
                         media_path=path_mappings.path_replace_movie(media_path),
                         subtitles_path=subtitles_path,
                         radarr_id=radarr_id)
        movies_download_subtitles(radarr_id)
        event_stream(type='movie-history')
        return '', 200

    @authenticate
    def delete(self):
        if request.args.get("all") == "true":
            blacklist_delete_all_movie()
        else:
            provider = request.form.get('provider')
            subs_id = request.form.get('subs_id')
            blacklist_delete_movie(provider=provider, subs_id=subs_id)
        return '', 200
