# coding=utf-8

import io
import json
import os
import logging

from flask import jsonify
from flask_restx import Resource, Namespace

from app.config import settings
from app.get_args import args

from ..utils import authenticate

api_ns_system_releases = Namespace('systemReleases', description='System releases API endpoint')


@api_ns_system_releases.route('system/releases')
class SystemReleases(Resource):
    @authenticate
    def get(self):
        filtered_releases = []
        try:
            with io.open(os.path.join(args.config_dir, 'config', 'releases.txt'), 'r', encoding='UTF-8') as f:
                releases = json.loads(f.read())

            for release in releases:
                if settings.general.branch == 'master' and not release['prerelease']:
                    filtered_releases.append(release)
                elif settings.general.branch != 'master' and any(not x['prerelease'] for x in filtered_releases):
                    continue
                elif settings.general.branch != 'master':
                    filtered_releases.append(release)
            if settings.general.branch == 'master':
                filtered_releases = filtered_releases[:5]

            current_version = os.environ["BAZARR_VERSION"]

            for i, release in enumerate(filtered_releases):
                body = release['body'].replace('- ', '').split('\n')[1:]
                filtered_releases[i] = {"body": body,
                                        "name": release['name'],
                                        "date": release['date'][:10],
                                        "prerelease": release['prerelease'],
                                        "current": release['name'].lstrip('v') == current_version}

        except Exception:
            logging.exception(
                'BAZARR cannot parse releases caching file: ' + os.path.join(args.config_dir, 'config', 'releases.txt'))
        return jsonify(data=filtered_releases)
