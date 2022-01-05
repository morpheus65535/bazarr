# coding=utf-8

import io
import os

from flask import jsonify
from flask_restful import Resource

from ..utils import authenticate
from logger import empty_log
from get_args import args


class SystemLogs(Resource):
    @authenticate
    def get(self):
        logs = []
        with io.open(os.path.join(args.config_dir, 'log', 'bazarr.log'), encoding='UTF-8') as file:
            raw_lines = file.read()
            lines = raw_lines.split('|\n')
            for line in lines:
                if line == '':
                    continue
                raw_message = line.split('|')
                raw_message_len = len(raw_message)
                if raw_message_len > 3:
                    log = dict()
                    log["timestamp"] = raw_message[0]
                    log["type"] = raw_message[1].rstrip()
                    log["message"] = raw_message[3]
                    if raw_message_len > 4 and raw_message[4] != '\n':
                        log['exception'] = raw_message[4].strip('\'').replace('  ', '\u2003\u2003')
                logs.append(log)

            logs.reverse()
        return jsonify(data=logs)

    @authenticate
    def delete(self):
        empty_log()
        return '', 204
