# coding=utf-8

from flask import request
from flask_restful import Resource

from app.database import TableEpisodes, TableShows
from get_subtitle.mass_download import episode_download_subtitles
from subtitles.indexer.series import store_subtitles
from utilities.helper import path_mappings

from ..utils import authenticate


class WebHooksSonarr(Resource):
    @authenticate
    def post(self):
        episode_file_id = request.form.get('sonarr_episodefile_id')

        sonarrEpisodeId = TableEpisodes.select(TableEpisodes.sonarrEpisodeId,
                                               TableEpisodes.path) \
            .join(TableShows, on=(TableEpisodes.sonarrSeriesId == TableShows.sonarrSeriesId)) \
            .where(TableEpisodes.episode_file_id == episode_file_id) \
            .dicts() \
            .get_or_none()

        if sonarrEpisodeId:
            store_subtitles(sonarrEpisodeId['path'], path_mappings.path_replace(sonarrEpisodeId['path']))
            episode_download_subtitles(no=sonarrEpisodeId['sonarrEpisodeId'], send_progress=True)

        return '', 200
