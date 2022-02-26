# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource
from subliminal_patch.core import guessit

from ..utils import authenticate


class SubtitleNameInfo(Resource):
    @authenticate
    def get(self):
        names = request.args.getlist('filenames[]')
        results = []
        for name in names:
            opts = dict()
            opts['type'] = 'episode'
            guessit_result = guessit(name, options=opts)
            result = {}
            result['filename'] = name
            if 'subtitle_language' in guessit_result:
                result['subtitle_language'] = str(guessit_result['subtitle_language'])

            result['episode'] = 0
            if 'episode' in guessit_result:
                if isinstance(guessit_result['episode'], list):
                    # for multiple episodes file, choose the first episode number
                    if len(guessit_result['episode']):
                        # make sure that guessit returned a list of more than 0 items
                        result['episode'] = int(guessit_result['episode'][0])
                elif isinstance(guessit_result['episode'], (str, int)):
                    # if single episode (should be int but just in case we cast it to int)
                    result['episode'] = int(guessit_result['episode'])

            if 'season' in guessit_result:
                result['season'] = int(guessit_result['season'])
            else:
                result['season'] = 0

            results.append(result)

        return jsonify(data=results)
