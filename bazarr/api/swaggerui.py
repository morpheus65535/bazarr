# coding=utf-8

import os

from flask_restx import fields

swaggerui_api_params = {"version": os.environ["BAZARR_VERSION"],
                        "description": "API docs for Bazarr",
                        "title": "Bazarr",
                        }

subtitles_model = {
        "name": fields.String(),
        "code2": fields.String(),
        "code3": fields.String(),
        "path": fields.String(),
        "forced": fields.Boolean(),
        "hi": fields.Boolean(),
        "file_size": fields.Integer(),
    }

subtitles_language_model = {
        "name": fields.String(),
        "code2": fields.String(),
        "code3": fields.String(),
        "forced": fields.Boolean(),
        "hi": fields.Boolean()
    }

audio_language_model = {
        "name": fields.String(),
        "code2": fields.String(),
        "code3": fields.String()
    }
