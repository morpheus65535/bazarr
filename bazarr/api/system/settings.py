# coding=utf-8

import json

from flask import request, jsonify
from flask_restful import Resource

from ..utils import authenticate
from database import TableLanguagesProfiles, TableSettingsLanguages, TableShows, TableMovies, TableSettingsNotifier, \
    update_profile_id_list
from event_handler import event_stream
from config import settings, save_settings, get_settings
from scheduler import scheduler
from list_subtitles import list_missing_subtitles, list_missing_subtitles_movies


class SystemSettings(Resource):
    @authenticate
    def get(self):
        data = get_settings()

        notifications = TableSettingsNotifier.select().order_by(TableSettingsNotifier.name).dicts()
        notifications = list(notifications)
        for i, item in enumerate(notifications):
            item["enabled"] = item["enabled"] == 1
            notifications[i] = item

        data['notifications'] = dict()
        data['notifications']['providers'] = notifications

        return jsonify(data)

    @authenticate
    def post(self):
        enabled_languages = request.form.getlist('languages-enabled')
        if len(enabled_languages) != 0:
            TableSettingsLanguages.update({
                TableSettingsLanguages.enabled: 0
            }).execute()
            for code in enabled_languages:
                TableSettingsLanguages.update({
                    TableSettingsLanguages.enabled: 1
                })\
                    .where(TableSettingsLanguages.code2 == code)\
                    .execute()
            event_stream("languages")

        languages_profiles = request.form.get('languages-profiles')
        if languages_profiles:
            existing_ids = TableLanguagesProfiles.select(TableLanguagesProfiles.profileId).dicts()
            existing_ids = list(existing_ids)
            existing = [x['profileId'] for x in existing_ids]
            for item in json.loads(languages_profiles):
                if item['profileId'] in existing:
                    # Update existing profiles
                    TableLanguagesProfiles.update({
                        TableLanguagesProfiles.name: item['name'],
                        TableLanguagesProfiles.cutoff: item['cutoff'] if item['cutoff'] != 'null' else None,
                        TableLanguagesProfiles.items: json.dumps(item['items']),
                        TableLanguagesProfiles.mustContain: item['mustContain'],
                        TableLanguagesProfiles.mustNotContain: item['mustNotContain'],
                    })\
                        .where(TableLanguagesProfiles.profileId == item['profileId'])\
                        .execute()
                    existing.remove(item['profileId'])
                else:
                    # Add new profiles
                    TableLanguagesProfiles.insert({
                        TableLanguagesProfiles.profileId: item['profileId'],
                        TableLanguagesProfiles.name: item['name'],
                        TableLanguagesProfiles.cutoff: item['cutoff'] if item['cutoff'] != 'null' else None,
                        TableLanguagesProfiles.items: json.dumps(item['items']),
                        TableLanguagesProfiles.mustContain: item['mustContain'],
                        TableLanguagesProfiles.mustNotContain: item['mustNotContain'],
                    }).execute()
            for profileId in existing:
                # Unassign this profileId from series and movies
                TableShows.update({
                    TableShows.profileId: None
                }).where(TableShows.profileId == profileId).execute()
                TableMovies.update({
                    TableMovies.profileId: None
                }).where(TableMovies.profileId == profileId).execute()
                # Remove deleted profiles
                TableLanguagesProfiles.delete().where(TableLanguagesProfiles.profileId == profileId).execute()

            update_profile_id_list()
            event_stream("languages")

            if settings.general.getboolean('use_series'):
                scheduler.add_job(list_missing_subtitles, kwargs={'send_event': False})
            if settings.general.getboolean('use_movies'):
                scheduler.add_job(list_missing_subtitles_movies, kwargs={'send_event': False})

        # Update Notification
        notifications = request.form.getlist('notifications-providers')
        for item in notifications:
            item = json.loads(item)
            TableSettingsNotifier.update({
                TableSettingsNotifier.enabled: item['enabled'],
                TableSettingsNotifier.url: item['url']
            }).where(TableSettingsNotifier.name == item['name']).execute()

        save_settings(zip(request.form.keys(), request.form.listvalues()))
        event_stream("settings")
        return '', 204
