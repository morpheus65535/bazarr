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
        radarrId = request.args.getlist('radarrid[]')

        count = TableMovies.select().count()

        if len(radarrId) != 0:
            result = TableMovies.select()\
                .where(TableMovies.radarrId.in_(radarrId))\
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
        radarrIdList = request.form.getlist('radarrid')
        profileIdList = request.form.getlist('profileid')

        for idx in range(len(radarrIdList)):
            radarrId = radarrIdList[idx]
            profileId = profileIdList[idx]

            if profileId in None_Keys:
                profileId = None
            else:
                try:
                    profileId = int(profileId)
                except Exception:
                    return '', 400

            TableMovies.update({
                TableMovies.profileId: profileId
            })\
                .where(TableMovies.radarrId == radarrId)\
                .execute()

            list_missing_subtitles_movies(no=radarrId, send_event=False)

            event_stream(type='movie', payload=radarrId)
            event_stream(type='movie-wanted', payload=radarrId)
        event_stream(type='badges')

        return '', 204

    @authenticate
    def patch(self):
        radarrid = request.form.get('radarrid')
        action = request.form.get('action')
        if action == "scan-disk":
            movies_scan_subtitles(radarrid)
            return '', 204
        elif action == "search-missing":
            movies_download_subtitles(radarrid)
            return '', 204
        elif action == "search-wanted":
            wanted_search_missing_subtitles_movies()
            return '', 204

        return '', 400
