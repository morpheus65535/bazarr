# coding=utf-8

import os
import platform

from flask import jsonify
from flask_restful import Resource

from radarr.info import get_radarr_info
from sonarr.info import get_sonarr_info
from app.get_args import args
from init import startTime

from ..utils import authenticate


class SystemStatus(Resource):
    @authenticate
    def get(self):
        package_version = ""
        if "BAZARR_PACKAGE_VERSION" in os.environ:
            package_version = os.environ["BAZARR_PACKAGE_VERSION"]
        if (
            "BAZARR_PACKAGE_AUTHOR" in os.environ
            and os.environ["BAZARR_PACKAGE_AUTHOR"] != ""
        ):
            package_version = (
                f'{package_version} by {os.environ["BAZARR_PACKAGE_AUTHOR"]}'
            )

        system_status = {
            "bazarr_version": os.environ["BAZARR_VERSION"],
            "package_version": package_version,
            "sonarr_version": get_sonarr_info.version(),
        }

        system_status["radarr_version"] = get_radarr_info.version()
        system_status["operating_system"] = platform.platform()
        system_status["python_version"] = platform.python_version()
        system_status["bazarr_directory"] = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )

        system_status["bazarr_config_directory"] = args.config_dir
        system_status["start_time"] = startTime

        return jsonify(data=system_status)
