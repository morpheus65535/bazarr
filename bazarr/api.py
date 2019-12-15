from flask import Flask, jsonify, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

import os
import ast
import libs

from get_args import args
from config import settings, url_sonarr, url_radarr, url_radarr_short, url_sonarr_short, base_url

from init import *
import logging
from database import database, dict_mapper
from helper import path_replace, path_replace_reverse, path_replace_movie, path_replace_reverse_movie
from get_languages import load_language_in_db, alpha2_from_language, alpha3_from_language, language_from_alpha2, \
    alpha3_from_alpha2

load_language_in_db()


class Badges(Resource):
    def get(self):
        result = {
            "missing_episodes": database.execute("SELECT COUNT(*) as count FROM table_episodes WHERE missing_subtitles "
                                                 "is not null AND missing_subtitles != '[]'", only_one=True)['count'],
            "missing_movies": database.execute("SELECT COUNT(*) as count FROM table_movies WHERE missing_subtitles "
                                               "is not null AND missing_subtitles != '[]'", only_one=True)['count'],
            "throttled_providers": len(eval(str(settings.general.throtteled_providers)))
        }
        return jsonify(result)


class Series(Resource):
    def get(self):
        seriesId = request.args.get('id')
        if seriesId:
            result = database.execute("SELECT * FROM table_shows WHERE sonarrSeriesId=?", (seriesId,))
        else:
            result = database.execute("SELECT * FROM table_shows")
        for item in result:
            # Parse audio language
            if item['audio_language']:
                item.update({"audio_language": {"name": item['audio_language'],
                                                "code2": alpha2_from_language(item['audio_language']),
                                                "code3": alpha3_from_language(item['audio_language'])}})

            # Parse desired languages
            if item['languages'] and item['languages'] != 'None':
                item.update({"languages": ast.literal_eval(item['languages'])})
                for i, subs in enumerate(item['languages']):
                    item['languages'][i] = {"name": language_from_alpha2(subs),
                                            "code2": subs,
                                            "code3": alpha3_from_alpha2(subs)}

            # Parse alternate titles
            if item['alternateTitles']:
                item.update({"alternateTitles": ast.literal_eval(item['alternateTitles'])})

            # Provide mapped path
            mapped_path = path_replace(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isdir(mapped_path)})

            # Add missing subtitles episode count
            item.update({"episodeMissingCount": database.execute("SELECT COUNT(*) as count FROM table_episodes WHERE "
                                                                 "sonarrSeriesId=? AND missing_subtitles is not null "
                                                                 "AND missing_subtitles != '[]'", (seriesId,),
                                                                 only_one=True)['count']})

            # Add episode count
            item.update({"episodeFileCount": database.execute("SELECT COUNT(*) as count FROM table_episodes WHERE "
                                                              "sonarrSeriesId=?", (seriesId,),
                                                              only_one=True)['count']})
        return jsonify(result)


class Episodes(Resource):
    def get(self):
        seriesId = request.args.get('id')
        if seriesId:
            result = database.execute("SELECT * FROM table_episodes WHERE sonarrSeriesId=?", (seriesId,))
        else:
            result = database.execute("SELECT * FROM table_episodes")
        for item in result:
            # Parse subtitles
            if item['subtitles']:
                item.update({"subtitles": ast.literal_eval(item['subtitles'])})
                for subs in item['subtitles']:
                    subs[0] = {"name": language_from_alpha2(subs[0]),
                               "code2": subs[0],
                               "code3": alpha3_from_alpha2(subs[0])}

            # Parse missing subtitles
            if item['missing_subtitles']:
                item.update({"missing_subtitles": ast.literal_eval(item['missing_subtitles'])})
                for i, subs in enumerate(item['missing_subtitles']):
                    item['missing_subtitles'][i] = {"name": language_from_alpha2(subs),
                                                    "code2": subs,
                                                    "code3": alpha3_from_alpha2(subs)}

            # Provide mapped path
            mapped_path = path_replace(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isfile(mapped_path)})
        return jsonify(result)


class Movies(Resource):
    def get(self):
        moviesId = request.args.get('id')
        if moviesId:
            result = database.execute("SELECT * FROM table_movies WHERE radarrId=?", (moviesId,))
        else:
            result = database.execute("SELECT * FROM table_movies")
        for item in result:
            # Parse audio language
            if item['audio_language']:
                item.update({"audio_language": {"name": item['audio_language'],
                                                "code2": alpha2_from_language(item['audio_language']),
                                                "code3": alpha3_from_language(item['audio_language'])}})

            # Parse desired languages
            if item['languages'] and item['languages'] != 'None':
                item.update({"languages": ast.literal_eval(item['languages'])})
                for i, subs in enumerate(item['languages']):
                    item['languages'][i] = {"name": language_from_alpha2(subs),
                                            "code2": subs,
                                            "code3": alpha3_from_alpha2(subs)}

            # Parse alternate titles
            if item['alternativeTitles']:
                item.update({"alternativeTitles": ast.literal_eval(item['alternativeTitles'])})

            # Parse failed attempts
            if item['failedAttempts']:
                item.update({"failedAttempts": ast.literal_eval(item['failedAttempts'])})

            # Parse subtitles
            if item['subtitles']:
                item.update({"subtitles": ast.literal_eval(item['subtitles'])})
                for subs in item['subtitles']:
                    subs[0] = {"name": language_from_alpha2(subs[0]),
                               "code2": subs[0],
                               "code3": alpha3_from_alpha2(subs[0])}

            # Parse missing subtitles
            if item['missing_subtitles']:
                item.update({"missing_subtitles": ast.literal_eval(item['missing_subtitles'])})
                for i, subs in enumerate(item['missing_subtitles']):
                    item['missing_subtitles'][i] = {"name": language_from_alpha2(subs),
                                                    "code2": subs,
                                                    "code3": alpha3_from_alpha2(subs)}

            # Provide mapped path
            mapped_path = path_replace_movie(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isfile(mapped_path)})
        return jsonify(result)


api.add_resource(Badges, '/api/badges')
api.add_resource(Series, '/api/series')
api.add_resource(Episodes, '/api/episodes')
api.add_resource(Movies, '/api/movies')

if __name__ == '__main__':
    app.run(debug=True)
