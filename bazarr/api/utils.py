# coding=utf-8

import ast

from functools import wraps
from flask import request, abort
from operator import itemgetter

from sqlalchemy import or_, and_

from app.config import settings, base_url
from languages.get_languages import language_from_alpha2, alpha3_from_alpha2
from app.database import (get_audio_profile_languages, get_desired_languages, get_subtitles, database, TableEpisodes,
                          TableShows, select)
from utilities.helper import bool_map
from utilities.path_mappings import path_mappings

None_Keys = ['null', 'undefined', '', None]

False_Keys = ['False', 'false', '0']


def profile_id_type(value):
    # reqparse type for the profileid filter: a profile ID or "none" to list
    # items without a languages profile. Raises ValueError (400) otherwise.
    if value == 'none':
        return value
    return int(value)


def add_list_query_args(parser):
    parser.add_argument('sort_by', type=str, required=False, default='title',
                        help='Column to sort by')
    parser.add_argument('sort_order', type=str, required=False, default='asc', choices=('asc', 'desc'),
                        help='Sort direction')
    parser.add_argument('monitored', type=str, required=False, choices=('true', 'false'),
                        help='Filter by monitored status')
    parser.add_argument('profileid', type=profile_id_type, required=False,
                        help='Filter by languages profile ID or "none"')
    parser.add_argument('missing', type=str, required=False, choices=('true', 'false'),
                        help='Filter by missing subtitles')
    parser.add_argument('audio_language', type=str, required=False,
                        help='Filter by audio language name')
    parser.add_argument('tags[]', type=str, action='append', required=False, default=[],
                        help='Tags to filter by')


def profile_filter_clause(column, value):
    if value == 'none':
        return column.is_(None)
    return column == value


def monitored_filter_clause(column, value):
    # monitored is stored as the string 'True'/'False', not a boolean
    return column == str(bool_map[value])


def tags_filter_clause(column, tags):
    # Tags are stored as a stringified list (e.g. "['tag1', 'tag2']"), match
    # any of the requested tags using the same pattern as get_exclusion_clause.
    return or_(*[column.contains(f"'{tag}'") for tag in tags])


def audio_language_filter_clause(column, language):
    # Audio languages are stored as a stringified list of language names
    # (e.g. "['English', 'French']").
    return column.contains(f"'{language}'")


def series_audio_language_filter_clause(language):
    # Series with an empty audio_language display the audio languages
    # aggregated from their episodes (see postprocess), so the filter must
    # match both the series value and the episodes values to stay consistent
    # with what the table shows.
    pattern = f"'{language}'"
    return or_(
        TableShows.audio_language.contains(pattern),
        and_(
            or_(TableShows.audio_language == '[]', TableShows.audio_language.is_(None)),
            TableShows.sonarrSeriesId.in_(
                select(TableEpisodes.sonarrSeriesId)
                .where(TableEpisodes.audio_language.contains(pattern))
            ),
        ),
    )


def apply_sort(stmt, sort_columns, default_column, sort_by, sort_order):
    # sort_columns is a whitelist of allowed sort columns; unknown sort_by
    # values fall back to the default column.
    sort_column = sort_columns.get(sort_by, default_column)
    return stmt.order_by(sort_column.asc() if sort_order == 'asc' else sort_column.desc())


def authenticate(actual_method):
    @wraps(actual_method)
    def wrapper(*args, **kwargs):
        apikey_settings = settings.auth.apikey
        apikey_get = request.args.get('apikey')
        apikey_post = request.form.get('apikey')
        apikey_header = None
        if 'X-API-KEY' in request.headers:
            apikey_header = request.headers['X-API-KEY']

        if apikey_settings in [apikey_get, apikey_post, apikey_header]:
            return actual_method(*args, **kwargs)

        return abort(401)

    return wrapper


def postprocess(item):
    # Remove ffprobe_cache
    if item.get('radarrId'):
        path_replace = path_mappings.path_replace_movie
    else:
        path_replace = path_mappings.path_replace
    if item.get('ffprobe_cache'):
        del item['ffprobe_cache']

    # Parse audio language
    if item.get('audio_language'):
        if item.get('sonarrSeriesId') and not item.get('sonarrEpisodeId') and item['audio_language'] == '[]':
            # if, for a series, audio_language is empty, we need to get the audio_language from the episodes
            episodes_audio_languages = database.execute(
                select(TableEpisodes.audio_language)
                .where(TableEpisodes.sonarrSeriesId == item['sonarrSeriesId'])
            ).scalars()

            # then parse the audio_languages for all episodes
            audio_languages_ast_list_of_lists = []
            for audio_languages in episodes_audio_languages:
                try:
                    audio_languages_ast_list_of_lists.append(ast.literal_eval(audio_languages))
                except ValueError:
                    print(toto)
                    continue

            # then flatten the list of lists as a set of unique audio languages
            audio_languages_flattened_set = set([item for sublist in audio_languages_ast_list_of_lists for item in sublist])

            # then convert the set to a string
            audio_languages_str = str(list(audio_languages_flattened_set))

            # to pass it to get_audio_profile_languages that will return a list of audio languages dicts
            item['audio_language'] = get_audio_profile_languages(audio_languages_str)
        else:
            # in other cases, we can directly pass the audio_language string to get_audio_profile_languages
            item['audio_language'] = get_audio_profile_languages(item['audio_language'])

    # Make sure profileId is a valid None value
    if item.get('profileId') in None_Keys:
        item['profileId'] = None

    # Parse alternate titles
    if item.get('alternativeTitles'):
        item['alternativeTitles'] = ast.literal_eval(item['alternativeTitles'])
    else:
        item['alternativeTitles'] = []

    # Add subtitles
    item['subtitles'] = get_subtitles(sonarr_episode_id=item.get('sonarrEpisodeId'),
                                      radarr_id=item.get('radarrId'))

    if settings.general.embedded_subs_show_desired and item.get('profileId'):
        desired_lang_list = get_desired_languages(item['profileId'])
        item['subtitles'] = [x for x in item['subtitles'] if x['code2'] in desired_lang_list or x['path']]
        item['subtitles'] = sorted(item['subtitles'], key=itemgetter('name', 'forced'))

    # Parse missing subtitles
    if item.get('missing_subtitles'):
        item['missing_subtitles'] = ast.literal_eval(item['missing_subtitles'])
        for i, subs in enumerate(item['missing_subtitles']):
            language = subs.split(':')
            item['missing_subtitles'][i] = {"name": language_from_alpha2(language[0]),
                                            "code2": language[0],
                                            "code3": alpha3_from_alpha2(language[0]),
                                            "forced": False,
                                            "hi": False}
            if len(language) > 1:
                item['missing_subtitles'][i].update(
                    {
                        "forced": language[1] == 'forced',
                        "hi": language[1] == 'hi',
                    }
                )
    else:
        item['missing_subtitles'] = []

    # Parse tags
    if item.get('tags') is not None:
        item['tags'] = ast.literal_eval(item.get('tags', '[]'))
    else:
        item['tags'] = []
    if item.get('monitored'):
        item['monitored'] = item.get('monitored') == 'True'
    else:
        item['monitored'] = False
    if item.get('hearing_impaired'):
        item['hearing_impaired'] = item.get('hearing_impaired') == 'True'
    else:
        item['hearing_impaired'] = False

    if item.get('language'):
        if item['language'] == 'None':
            item['language'] = None
        if item['language'] is not None:
            splitted_language = item['language'].split(':')
            item['language'] = {
                "name": language_from_alpha2(splitted_language[0]),
                "code2": splitted_language[0],
                "code3": alpha3_from_alpha2(splitted_language[0]),
                "forced": bool(item['language'].endswith(':forced')),
                "hi": bool(item['language'].endswith(':hi')),
            }

    if item.get('path'):
        item['path'] = path_replace(item['path'])

    if item.get('video_path'):
        # Provide mapped video path for history
        item['video_path'] = path_replace(item['video_path'])

    if item.get('subtitles_path'):
        # Provide mapped subtitles path
        item['subtitles_path'] = path_replace(item['subtitles_path'])

    if item.get('external_subtitles'):
        # Provide mapped external subtitles paths for history
        item['external_subtitles'] = path_replace(item['external_subtitles'])

    # map poster and fanart to server proxy
    if item.get('poster') is not None:
        poster = item['poster']
        item['poster'] = f"{base_url}/images/{'movies' if item.get('radarrId') else 'series'}{poster}" if poster else None

    if item.get('fanart') is not None:
        fanart = item['fanart']
        item['fanart'] = f"{base_url}/images/{'movies' if item.get('radarrId') else 'series'}{fanart}" if fanart else None

    return item
