# coding=utf-8

from flask import request, jsonify
from flask_restful import Resource

from operator import itemgetter

from ..utils import authenticate, False_Keys
from database import TableHistory, TableHistoryMovie, TableSettingsLanguages
from get_languages import alpha2_from_alpha3, language_from_alpha2


class Languages(Resource):
    @authenticate
    def get(self):
        history = request.args.get('history')
        if history and history not in False_Keys:
            languages = list(TableHistory.select(TableHistory.language)
                             .where(TableHistory.language is not None)
                             .dicts())
            languages += list(TableHistoryMovie.select(TableHistoryMovie.language)
                              .where(TableHistoryMovie.language is not None)
                              .dicts())
            languages_list = list(set([lang['language'].split(':')[0] for lang in languages]))
            languages_dicts = []
            for language in languages_list:
                code2 = None
                if len(language) == 2:
                    code2 = language
                elif len(language) == 3:
                    code2 = alpha2_from_alpha3(language)
                else:
                    continue

                if not any(x['code2'] == code2 for x in languages_dicts):
                    try:
                        languages_dicts.append({
                            'code2': code2,
                            'name': language_from_alpha2(code2),
                            # Compatibility: Use false temporarily
                            'enabled': False
                        })
                    except Exception:
                        continue
            return jsonify(sorted(languages_dicts, key=itemgetter('name')))

        result = TableSettingsLanguages.select(TableSettingsLanguages.name,
                                               TableSettingsLanguages.code2,
                                               TableSettingsLanguages.enabled)\
            .order_by(TableSettingsLanguages.name).dicts()
        result = list(result)
        for item in result:
            item['enabled'] = item['enabled'] == 1
        return jsonify(result)
