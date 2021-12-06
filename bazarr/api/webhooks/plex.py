# coding=utf-8

import json
import requests
import os
import re

from flask import request
from flask_restful import Resource
from bs4 import BeautifulSoup as bso

from database import TableEpisodes, TableShows, TableMovies
from get_subtitle import episode_download_subtitles, movies_download_subtitles
from ..utils import authenticate


class WebHooksPlex(Resource):
    @authenticate
    def post(self):
        json_webhook = request.form.get('payload')
        parsed_json_webhook = json.loads(json_webhook)

        event = parsed_json_webhook['event']
        if event not in ['media.play']:
            return '', 204

        media_type = parsed_json_webhook['Metadata']['type']

        if media_type == 'episode':
            season = parsed_json_webhook['Metadata']['parentIndex']
            episode = parsed_json_webhook['Metadata']['index']
        else:
            season = episode = None

        ids = []
        for item in parsed_json_webhook['Metadata']['Guid']:
            splitted_id = item['id'].split('://')
            if len(splitted_id) == 2:
                ids.append({splitted_id[0]: splitted_id[1]})
        if not ids:
            return '', 404

        if media_type == 'episode':
            try:
                episode_imdb_id = [x['imdb'] for x in ids if 'imdb' in x][0]
                r = requests.get('https://imdb.com/title/{}'.format(episode_imdb_id),
                                 headers={"User-Agent": os.environ["SZ_USER_AGENT"]})
                soup = bso(r.content, "html.parser")
                series_imdb_id = soup.find('a', {'class': re.compile(r'SeriesParentLink__ParentTextLink')})['href'].split('/')[2]
            except Exception:
                return '', 404
            else:
                episodeId = TableEpisodes.select(TableEpisodes.episodeId) \
                    .join(TableShows) \
                    .where(TableShows.imdbId == series_imdb_id,
                           TableEpisodes.season == season,
                           TableEpisodes.episode == episode) \
                    .dicts() \
                    .get()

                if episodeId:
                    episode_download_subtitles(no=episodeId['episodeId'], send_progress=True)
        else:
            try:
                movie_imdb_id = [x['imdb'] for x in ids if 'imdb' in x][0]
            except Exception:
                return '', 404
            else:
                movieId = TableMovies.select(TableMovies.movieId)\
                    .where(TableMovies.imdbId == movie_imdb_id)\
                    .dicts()\
                    .get()
                if movieId:
                    movies_download_subtitles(no=movieId['movieId'])

        return '', 200
