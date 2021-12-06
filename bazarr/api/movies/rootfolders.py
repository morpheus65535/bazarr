# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from ..utils import authenticate
from database import TableMoviesRootfolder


class MoviesRootfolders(Resource):
    @authenticate
    def get(self):
        # list existing movies root folders
        root_folders = TableMoviesRootfolder.select().dicts()
        root_folders = list(root_folders)
        return jsonify(data=root_folders)

    @authenticate
    def post(self):
        # add a new movies root folder
        path = request.form.get('path')
        result = TableMoviesRootfolder.insert({
            TableMoviesRootfolder.path: path,
            TableMoviesRootfolder.accessible: 1,  # TODO: test it instead of assuming it's accessible
            TableMoviesRootfolder.error: ''
        }).execute()
        return jsonify(data=list(TableMoviesRootfolder.select().where(TableMoviesRootfolder.rootId == result).dicts()))
