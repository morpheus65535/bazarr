# coding=utf-8

import json

from flask import request, jsonify
from flask_restx import Resource, Namespace
from dynaconf.validator import ValidationError

from api.utils import None_Keys
from app.database import TableLanguagesProfiles, TableSettingsLanguages, TableSettingsNotifier, \
    update_profile_id_list, database, insert, update, delete, select
from app.event_handler import event_stream
from app.config import settings, save_settings, get_settings
from app.scheduler import scheduler
from subtitles.indexer.series import list_missing_subtitles
from subtitles.indexer.movies import list_missing_subtitles_movies

from ..utils import authenticate

api_ns_system_settings = Namespace('systemSettings', description='System settings API endpoint')


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

        languages_profiles = request.form.get('languages-profiles')
        if languages_profiles:
            existing_ids = database.execute(
                select(TableLanguagesProfiles.profileId))\
                .all()
            existing = [x.profileId for x in existing_ids]
            for item in json.loads(languages_profiles):
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
                scheduler.add_job(list_missing_subtitles, kwargs={'send_event': True})
            if settings.general.use_radarr:
                scheduler.add_job(list_missing_subtitles_movies, kwargs={'send_event': True})

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
