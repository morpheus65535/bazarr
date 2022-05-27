# coding=utf-8

from flask import jsonify, request
from flask_restful import Resource

from utilities.backup import (
    get_backup_files,
    prepare_restore,
    delete_backup_file,
    backup_to_zip,
)

from ..utils import authenticate


class SystemBackups(Resource):
    @authenticate
    def get(self):
        backups = get_backup_files(fullpath=False)
        return jsonify(data=backups)

    @authenticate
    def post(self):
        backup_to_zip()
        return "", 204

    @authenticate
    def patch(self):
        if filename := request.form.get("filename"):
            if restored := prepare_restore(filename):
                return "", 204
        return "", 501

    @authenticate
    def delete(self):
        if filename := request.form.get("filename"):
            if deleted := delete_backup_file(filename):
                return "", 204
        return "", 501
