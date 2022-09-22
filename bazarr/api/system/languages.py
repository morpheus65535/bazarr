# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields
from operator import itemgetter

from app.database import TableHistory, TableHistoryMovie, TableSettingsLanguages
from languages.get_languages import alpha2_from_alpha3, language_from_alpha2

from ..utils import authenticate, False_Keys

api_ns_system_languages = Namespace('System Languages', description='Get languages list')


@api_ns_system_languages.route('system/languages')
class Languages(Resource):
    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('history', type=str, required=False, help='Language name for history stats')

    @authenticate
    @api_ns_system_languages.doc(parser=get_request_parser)
    @api_ns_system_languages.response(200, 'Success')
    @api_ns_system_languages.response(401, 'Not Authenticated')
    def get(self):
        """List languages for history filter or for language filter menu"""
        args = self.get_request_parser.parse_args()
        history = args.get('history')
        if history and history not in False_Keys:
            languages = list(TableHistory.select(TableHistory.language)
                             .where(TableHistory.language.is_null(False))
                             .dicts())
            languages += list(TableHistoryMovie.select(TableHistoryMovie.language)
                              .where(TableHistoryMovie.language.is_null(False))
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
        else:
            languages_dicts = TableSettingsLanguages.select(TableSettingsLanguages.name,
                                                            TableSettingsLanguages.code2,
                                                            TableSettingsLanguages.enabled)\
                .order_by(TableSettingsLanguages.name).dicts()
            languages_dicts = list(languages_dicts)
            for item in languages_dicts:
                item['enabled'] = item['enabled'] == 1

        return sorted(languages_dicts, key=itemgetter('name'))
