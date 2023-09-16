# coding=utf-8

import io
import json
import os
import logging

from flask_restx import Resource, Namespace, fields, marshal

from app.config import settings
from app.get_args import args

from ..utils import authenticate

api_ns_system_releases = Namespace('System Releases', description='List Bazarr releases from Github')


@api_ns_system_releases.route('system/releases')
class SystemReleases(Resource):
    get_response_model = api_ns_system_releases.model('SystemBackupsGetResponse', {
        'body': fields.List(fields.String),
        'name': fields.String(),
        'date': fields.String(),
        'prerelease': fields.Boolean(),
        'current': fields.Boolean(),
    })

    @authenticate
    @api_ns_system_releases.doc(parser=None)
    @api_ns_system_releases.response(200, 'Success')
    @api_ns_system_releases.response(401, 'Not Authenticated')
    def get(self):
        """Get Bazarr releases"""
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
        return marshal(filtered_releases, self.get_response_model, envelope='data')
