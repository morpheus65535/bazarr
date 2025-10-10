# coding=utf-8

from flask_restx import Namespace
api_ns_plex = Namespace('Plex Authentication', description='Plex OAuth and server management')

from .oauth import *  # noqa
api_ns_list_plex = [api_ns_plex]
