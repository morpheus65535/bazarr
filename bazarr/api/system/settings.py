# coding=utf-8

import json

from flask import request, jsonify
from flask_restx import Resource, Namespace
from dynaconf.validator import ValidationError

from api.utils import None_Keys
from app.database import TableLanguagesProfiles, TableSettingsLanguages, TableSettingsNotifier, \
    update_profile_id_list, database, insert, update, delete, select, PROFILE_TYPE_BASIC, PROFILE_TYPE_ENHANCED
from app.event_handler import event_stream
from app.config import settings, save_settings, get_settings
from app.scheduler import scheduler
from subtitles.indexer.series import list_missing_subtitles
from subtitles.indexer.movies import list_missing_subtitles_movies

from ..utils import authenticate

api_ns_system_settings = Namespace('systemSettings', description='System settings API endpoint')

ANY_CUTOFF = 65535
GROUP_OPERATORS = ('AND', 'OR')
ITEM_HI_VALUES = ('True', 'False', 'Excluded')
ITEM_BOOLEAN_VALUES = ('True', 'False')


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _enhanced_item_error(item):
    if not isinstance(item, dict):
        return 'a language must be an object'
    if not _is_int(item.get('id')):
        return 'a language has an invalid id'
    if not isinstance(item.get('language'), str) or not item['language']:
        return f"language {item['id']} has no language code"
    if item.get('hi') not in ITEM_HI_VALUES:
        return f"language {item['id']} has an invalid hearing-impaired value"
    for field in ('forced', 'audio_exclude', 'audio_only_include'):
        if item.get(field) not in ITEM_BOOLEAN_VALUES:
            return f"language {item['id']} has an invalid {field} value"
    return None


def _enhanced_profile_error(profile):
    groups = profile.get('items', {}).get('groups') if isinstance(profile.get('items'), dict) else None
    if not isinstance(groups, list) or not groups:
        return 'it must have at least one group'

    group_ids = []
    item_ids = []
    for group in groups:
        if not isinstance(group, dict):
            return 'a group must be an object'
        group_id = group.get('id')
        if not _is_int(group_id) or group_id == ANY_CUTOFF:
            return f'group id {group_id!r} is invalid'
        if group_id in group_ids:
            return f'group id {group_id} is used more than once'
        group_ids.append(group_id)

        if group.get('operator') not in GROUP_OPERATORS:
            return f'group {group_id} has an invalid operator'
        group_items = group.get('items')
        if not isinstance(group_items, list) or not group_items:
            return f'group {group_id} must have at least one language'
        for item in group_items:
            error = _enhanced_item_error(item)
            if error:
                return f'group {group_id}: {error}'
            if item['id'] in item_ids:
                return f"language id {item['id']} is used more than once"
            item_ids.append(item['id'])

    cutoff = profile.get('cutoff')
    if cutoff not in None_Keys and cutoff != ANY_CUTOFF and cutoff not in group_ids:
        return f'cutoff {cutoff!r} does not match a group'
    return None


def validate_languages_profiles(profiles):
    """
    Return an error message for the first invalid profile, or None if all are valid.

    Only enhanced profiles are checked here. Basic profiles keep their existing handling.
    """
    for profile in profiles:
        name = profile.get('name')
        profile_type = profile.get('profileType', PROFILE_TYPE_BASIC)
        if profile_type not in (PROFILE_TYPE_BASIC, PROFILE_TYPE_ENHANCED):
            return f'Languages profile {name!r} has an unknown profile type {profile_type!r}'
        if profile_type == PROFILE_TYPE_ENHANCED:
            error = _enhanced_profile_error(profile)
            if error:
                return f'Languages profile {name!r} is invalid: {error}'
    return None


@api_ns_system_settings.hide
@api_ns_system_settings.route('system/settings')
class SystemSettings(Resource):
    @authenticate
    def get(self):
        data = get_settings()
        data['notifications'] = dict()
        data['notifications']['providers'] = [{
            'name': x.name,
            'enabled': x.enabled == 1,
            'url': x.url
        } for x in database.execute(
            select(TableSettingsNotifier.name,
                   TableSettingsNotifier.enabled,
                   TableSettingsNotifier.url)
            .order_by(TableSettingsNotifier.name))
            .all()]

        return jsonify(data)

    @authenticate
    def post(self):
        languages_profiles = request.form.get('languages-profiles')
        profiles_to_save = json.loads(languages_profiles) if languages_profiles else None
        if profiles_to_save is not None:
            # Validate before any write, so a rejected payload leaves the settings untouched.
            error = validate_languages_profiles(profiles_to_save)
            if error:
                return error, 400

        enabled_languages = request.form.getlist('languages-enabled')
        if len(enabled_languages) != 0:
            database.execute(
                update(TableSettingsLanguages)
                .values(enabled=0))
            for code in enabled_languages:
                database.execute(
                    update(TableSettingsLanguages)
                    .values(enabled=1)
                    .where(TableSettingsLanguages.code2 == code))
            event_stream("languages")

        if profiles_to_save is not None:
            existing_ids = database.execute(
                select(TableLanguagesProfiles.profileId))\
                .all()
            existing = [x.profileId for x in existing_ids]
            for item in profiles_to_save:
                if item['profileId'] in existing:
                    # Update existing profiles
                    database.execute(
                        update(TableLanguagesProfiles)
                        .values(
                            name=item['name'],
                            cutoff=item['cutoff'] if item['cutoff'] not in None_Keys else None,
                            items=json.dumps(item['items']),
                            mustContain=str(item['mustContain']),
                            mustNotContain=str(item['mustNotContain']),
                            originalFormat=int(item['originalFormat']) if item['originalFormat'] not in None_Keys else
                            None,
                            tag=item['tag'] if 'tag' in item else None,
                            profileType=item.get('profileType', PROFILE_TYPE_BASIC),
                        )
                        .where(TableLanguagesProfiles.profileId == item['profileId']))
                    existing.remove(item['profileId'])
                else:
                    # Add new profiles
                    database.execute(
                        insert(TableLanguagesProfiles)
                        .values(
                            profileId=item['profileId'],
                            name=item['name'],
                            cutoff=item['cutoff'] if item['cutoff'] not in None_Keys else None,
                            items=json.dumps(item['items']),
                            mustContain=str(item['mustContain']),
                            mustNotContain=str(item['mustNotContain']),
                            originalFormat=int(item['originalFormat']) if item['originalFormat'] not in None_Keys else
                            None,
                            tag=item['tag'] if 'tag' in item else None,
                            profileType=item.get('profileType', PROFILE_TYPE_BASIC),
                        ))
            for profileId in existing:
                # Remove deleted profiles
                database.execute(
                    delete(TableLanguagesProfiles)
                    .where(TableLanguagesProfiles.profileId == profileId))

            # invalidate cache
            update_profile_id_list.invalidate()

            event_stream("languages")

            if settings.general.use_sonarr:
                list_missing_subtitles()
            if settings.general.use_radarr:
                list_missing_subtitles_movies()

        # Update Notification
        notifications = request.form.getlist('notifications-providers')
        for item in notifications:
            item = json.loads(item)
            database.execute(
                update(TableSettingsNotifier).values(
                    enabled=int(item['enabled'] is True),
                    url=item['url'])
                .where(TableSettingsNotifier.name == item['name']))

        try:
            save_settings(zip(request.form.keys(), request.form.listvalues()))
        except ValidationError as e:
            event_stream("settings")
            return e.message, 406
        else:
            event_stream("settings")
            return '', 204


@api_ns_system_settings.route('system/webhooks/test')
class SystemWebhookTest(Resource):
    @authenticate
    def post(self):
        """Test external webhook connection."""
        try:
            from utilities.autopulse_webhook import test_external_webhook_connection
            
            success, message = test_external_webhook_connection()
            
            return {
                'data': {
                    'success': success,
                    'message': message
                }
            }
            
        except Exception as e:
            return {
                'data': {
                    'success': False,
                    'message': f'Failed to test webhook: {str(e)}'
                }
            }, 400
