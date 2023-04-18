# coding=utf-8

import json

from flask import request, jsonify
from flask_restx import Resource, Namespace

from app.database import TableLanguagesProfiles, TableSettingsLanguages, TableShows, TableMovies, \
    TableSettingsNotifier, update_profile_id_list, database, rows_as_list_of_dicts, insert, update, delete
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

        notifications = rows_as_list_of_dicts(database.query(TableSettingsNotifier.name,
                                                             TableSettingsNotifier.enabled,
                                                             TableSettingsNotifier.url)
                                              .order_by(TableSettingsNotifier.name).all())
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
            database.execute(update(TableSettingsLanguages).vaues(enabled=0))
            for code in enabled_languages:
                database.execute(update(TableSettingsLanguages).values(enabled=1))\
                    .where(TableSettingsLanguages.code2 == code)
            event_stream("languages")
        database.commit()

        languages_profiles = request.form.get('languages-profiles')
        if languages_profiles:
            existing_ids = database.query(TableLanguagesProfiles.profileId).all()
            existing = [x.profileId for x in existing_ids]
            for item in json.loads(languages_profiles):
                if item.profileId in existing:
                    # Update existing profiles
                    database.execute(update(TableLanguagesProfiles).values(
                        name=item.name,
                        cutoff=item.cutoff if item.cutoff != 'null' else None,
                        items=json.dumps(item.items),
                        mustContain=item.mustContain,
                        mustNotContain=item.mustNotContain,
                        originalFormat=item.originalFormat if item.originalFormat != 'null' else None,
                    )
                                     .where(TableLanguagesProfiles.profileId == item.profileId))
                    existing.remove(item.profileId)
                else:
                    # Add new profiles
                    database.execute(insert(TableLanguagesProfiles).values(
                        profileId=item.profileId,
                        name=item.name,
                        cutoff=item.cutoff if item.cutoff != 'null' else None,
                        items=json.dumps(item.items),
                        mustContain=item.mustContain,
                        mustNotContain=item.mustNotContain,
                        originalFormat=item.originalFormat if item.originalFormat != 'null' else None,
                    ))
            for profileId in existing:
                # Remove deleted profiles
                database.execute(delete(TableLanguagesProfiles).where(TableLanguagesProfiles.profileId == profileId))

            database.commit()

            # invalidate cache
            update_profile_id_list.invalidate()

            event_stream("languages")

            if settings.general.getboolean('use_sonarr'):
                scheduler.add_job(list_missing_subtitles, kwargs={'send_event': True})
            if settings.general.getboolean('use_radarr'):
                scheduler.add_job(list_missing_subtitles_movies, kwargs={'send_event': True})

        # Update Notification
        notifications = request.form.getlist('notifications-providers')
        for item in notifications:
            item = json.loads(item)
            database.execute(update(TableSettingsNotifier).values(
                enabled=item['enabled'],
                url=item['url'])
                             .where(TableSettingsNotifier.name == item['name']))
        database.commit()

        save_settings(zip(request.form.keys(), request.form.listvalues()))
        event_stream("settings")
        return '', 204
