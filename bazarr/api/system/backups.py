# coding=utf-8

from flask import jsonify, request
from flask_restful import Resource

from ..utils import authenticate
from backup import get_backup_files, prepare_restore, delete_backup_file


class SystemBackups(Resource):
    @authenticate
    def get(self):
        backups = get_backup_files(fullpath=False)
        return jsonify(data=backups)

    @authenticate
    def post(self):
        filename = request.form.get('filename')
        if filename:
            restored = prepare_restore(filename)
            if restored:
                return '', 204
        return '', 501

    @authenticate
    def delete(self):
        filename = request.form.get('filename')
        if filename:
            deleted = delete_backup_file(filename)
            if deleted:
                return '', 204
        return '', 501
