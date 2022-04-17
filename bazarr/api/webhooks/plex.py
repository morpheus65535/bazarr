# coding=utf-8

import json
import requests
import os
import logging

from flask import request
from flask_restful import Resource
from bs4 import BeautifulSoup as bso

from bazarr.database import TableEpisodes, TableShows, TableMovies
from bazarr.get_subtitle.mass_download import episode_download_subtitles, movies_download_subtitles

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
                script_tag = soup.find(id='__NEXT_DATA__')
                script_tag_json = script_tag.string
                show_metadata_dict = json.loads(script_tag_json)
                series_imdb_id = show_metadata_dict['props']['pageProps']['aboveTheFoldData']['series']['series']['id']
            except Exception:
                logging.debug('BAZARR is unable to get series IMDB id.')
                return '', 404
            else:
                sonarrEpisodeId = TableEpisodes.select(TableEpisodes.sonarrEpisodeId) \
                    .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)) \
                    .where(TableShows.imdbId == series_imdb_id,
                           TableEpisodes.season == season,
                           TableEpisodes.episode == episode) \
                    .dicts() \
                    .get_or_none()

                if sonarrEpisodeId:
                    episode_download_subtitles(no=sonarrEpisodeId['sonarrEpisodeId'], send_progress=True)
        else:
            try:
                movie_imdb_id = [x['imdb'] for x in ids if 'imdb' in x][0]
            except Exception:
                return '', 404
            else:
                radarrId = TableMovies.select(TableMovies.radarrId)\
                    .where(TableMovies.imdbId == movie_imdb_id)\
                    .dicts()\
                    .get_or_none()

                if radarrId:
                    movies_download_subtitles(no=radarrId['radarrId'])

        return '', 200
