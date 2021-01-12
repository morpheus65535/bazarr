#!/bin/env python
from flask import Flask, redirect, render_template, request, url_for
from flask_debugtoolbar import DebugToolbarExtension
from flask_socketio import SocketIO
import os

from get_args import args
from config import settings, base_url

socketio = SocketIO()


def create_app():
    # Flask Setup
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), '..', 'views'),
                static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
                static_url_path=base_url.rstrip('/') + '/static')
    app.wsgi_app = ReverseProxied(app.wsgi_app)
    app.route = prefix_route(app.route, base_url.rstrip('/'))

    app.config["SECRET_KEY"] = settings.general.flask_secret_key
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.config['JSON_AS_ASCII'] = False

    if args.dev:
        app.config["DEBUG"] = True
        # Flask-Debuger
        app.config["DEBUG_TB_ENABLED"] = True
        app.config["DEBUG_TB_PROFILER_ENABLED"] = True
        app.config["DEBUG_TB_TEMPLATE_EDITOR_ENABLED"] = True
        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
    else:
        app.config["DEBUG"] = False
        # Flask-Debuger
        app.config["DEBUG_TB_ENABLED"] = False

    toolbar = DebugToolbarExtension(app)

    socketio.init_app(app, path=base_url.rstrip('/')+'/socket.io', cors_allowed_origins='*', async_mode='threading')
    return app


def prefix_route(route_function, prefix='', mask='{0}{1}'):
    # Defines a new route function with a prefix.
    # The mask argument is a `format string` formatted with, in that order: prefix, route
    def newroute(route, *args, **kwargs):
        # New function to prefix the route
        return route_function(mask.format(prefix, route), *args, **kwargs)

    return newroute


class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)
