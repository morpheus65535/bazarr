# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from ..utils import authenticate
from database import TableShowsRootfolder


class SeriesRootfolders(Resource):
    @authenticate
    def get(self):
        # list existing series root folders
        root_folders = TableShowsRootfolder.select().dicts()
        root_folders = list(root_folders)
        return jsonify(data=root_folders)

    @authenticate
    def post(self):
        # add a new series root folder
        path = request.form.get('path')
        result = TableShowsRootfolder.insert({
            TableShowsRootfolder.path: path,
            TableShowsRootfolder.accessible: 1,  # TODO: test it instead of assuming it's accessible
            TableShowsRootfolder.error: ''
        }).execute()
        return jsonify(data=list(TableShowsRootfolder.select().where(TableShowsRootfolder.rootId == result).dicts()))
