# coding=utf-8

import datetime
import pretty

from flask import request, jsonify
from flask_restful import Resource

from database import TableMovies, TableBlacklistMovie
from ..utils import authenticate, postprocessMovie
from utils import blacklist_log_movie, delete_subtitles, blacklist_delete_all_movie, blacklist_delete_movie
from get_subtitle import movies_download_subtitles
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
                                          TableMovies.movieId,
                                          TableBlacklistMovie.provider,
                                          TableBlacklistMovie.subs_id,
                                          TableBlacklistMovie.language,
                                          TableBlacklistMovie.timestamp)\
            .join(TableMovies)\
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
        movie_id = int(request.args.get('movieid'))
        provider = request.form.get('provider')
        subs_id = request.form.get('subs_id')
        language = request.form.get('language')
        # TODO
        forced = False
        hi = False

        data = TableMovies.select(TableMovies.path).where(TableMovies.movieId == movie_id).dicts().get()

        media_path = data['path']
        subtitles_path = request.form.get('subtitles_path')

        blacklist_log_movie(movie_id=movie_id,
                            provider=provider,
                            subs_id=subs_id,
                            language=language)
        delete_subtitles(media_type='movie',
                         language=language,
                         forced=forced,
                         hi=hi,
                         media_path=media_path,
                         subtitles_path=subtitles_path,
                         movie_id=movie_id)
        movies_download_subtitles(movie_id)
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
