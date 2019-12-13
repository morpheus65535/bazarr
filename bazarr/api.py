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
from get_languages import load_language_in_db, alpha2_from_language, alpha3_from_language

load_language_in_db()

class Series(Resource):
    def get(self):
        seriesId = request.args.get('id')
        if seriesId:
            result = database.execute("SELECT * FROM table_shows WHERE sonarrSeriesId=?", (seriesId,))
        else:
            result = database.execute("SELECT * FROM table_shows")
        for item in result:
            # Parse audio language
            item.update({"audio_language": {"name": item['audio_language'],
                                            "code2": alpha2_from_language(item['audio_language']),
                                            "code3": alpha3_from_language(item['audio_language'])}})

            # Parse desired languages
            item.update({"languages": ast.literal_eval(item['languages'])})

            # Parse alternate titles
            item.update({"alternateTitles": ast.literal_eval(item['alternateTitles'])})

            # Provide mapped path
            mapped_path = path_replace(item['path'])
            item.update({"mapped_path": mapped_path})

            # Confirm if path exist
            item.update({"exist": os.path.isdir(mapped_path)})
        return jsonify(result)


api.add_resource(Series, '/api/series')

if __name__ == '__main__':
    app.run(debug=True)
