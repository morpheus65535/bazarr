# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from database import TableMovies
from ..utils import authenticate, postprocessMovie, None_Keys
from list_subtitles import list_missing_subtitles_movies, movies_scan_subtitles
from event_handler import event_stream
from get_subtitle import movies_download_subtitles, wanted_search_missing_subtitles_movies


class Movies(Resource):
    @authenticate
    def get(self):
        start = request.args.get('start') or 0
        length = request.args.get('length') or -1
        movieId = request.args.getlist('movieid[]')

        count = TableMovies.select().count()

        if len(movieId) != 0:
            result = TableMovies.select()\
                .where(TableMovies.movieId.in_(movieId))\
                .order_by(TableMovies.sortTitle)\
                .dicts()
        else:
            result = TableMovies.select().order_by(TableMovies.sortTitle).limit(length).offset(start).dicts()
        result = list(result)
        for item in result:
            postprocessMovie(item)

        return jsonify(data=result, total=count)

    @authenticate
    def post(self):
        movieIdList = request.form.getlist('movieid')
        profileIdList = request.form.getlist('profileid')
        monitoredList = request.form.getlist('monitored')

        for idx in range(len(movieIdList)):
            movieId = movieIdList[idx]
            profileId = profileIdList[idx]
            monitored = monitoredList[idx]

            if profileId in None_Keys:
                profileId = None
            else:
                try:
                    profileId = int(profileId)
                except Exception:
                    return '', 400

            TableMovies.update({
                TableMovies.profileId: profileId,
                TableMovies.monitored: monitored
            })\
                .where(TableMovies.movieId == movieId)\
                .execute()

            list_missing_subtitles_movies(no=movieId, send_event=False)

            event_stream(type='movie', payload=movieId)
            event_stream(type='movie-wanted', payload=movieId)
        event_stream(type='badges')

        return '', 204

    @authenticate
    def patch(self):
        movieid = request.form.get('movieid')
        action = request.form.get('action')
        value = request.form.get('value')
        tmdbid = request.form.get('tmdbid')
        if tmdbid:
            TableMovies.update({TableMovies.tmdbId: tmdbid}).where(TableMovies.movieId == movieid).execute()
            event_stream(type='movie', payload=movieid)
            movies_scan_subtitles(movieid)
            return '', 204
        elif action == "refresh":
            movies_scan_subtitles(movieid)
            return '', 204
        elif action == "search-missing":
            movies_download_subtitles(movieid)
            return '', 204
        elif action == "search-wanted":
            wanted_search_missing_subtitles_movies()
            return '', 204
        elif action == "monitored":
            if value == 'false':
                new_monitored_value = 'True'
            else:
                new_monitored_value = 'False'

            TableMovies.update({
                TableMovies.monitored: new_monitored_value
            }) \
                .where(TableMovies.movieId == movieid) \
                .execute()

            event_stream(type='movie', payload=movieid)
            event_stream(type='badges')
            event_stream(type='movie-wanted')

            return '', 204

        return '', 400
