# coding=utf-8

from flask import request
from flask_restful import Resource

from ..utils import authenticate
from indexer.series.local.series_indexer import get_series_metadata
from database import TableShows
from list_subtitles import store_subtitles


class SeriesAdd(Resource):
    @authenticate
    def post(self):
        # add a new series to database
        tmdbId = request.args.get('tmdbid')
        rootdir_id = request.args.get('rootdir_id')
        directory = request.args.get('directory')
        series_metadata = get_series_metadata(tmdbid=tmdbId, root_dir_id=rootdir_id, dir_name=directory)
        if series_metadata and series_metadata['path']:
            try:
                result = TableShows.insert(series_metadata).execute()
            except Exception:
                pass
            else:
                if result:
                    store_subtitles(series_metadata['path'])
