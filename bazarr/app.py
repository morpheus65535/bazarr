# coding=utf-8

from flask import Flask
from flask_socketio import SocketIO
import os

from get_args import args
from config import settings, base_url

socketio = SocketIO()


def create_app():
    # Flask Setup
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build'),
                static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build', 'static'),
                static_url_path=base_url.rstrip('/') + '/static')
    app.wsgi_app = ReverseProxied(app.wsgi_app)
    app.route = prefix_route(app.route, base_url.rstrip('/'))

    app.config["SECRET_KEY"] = settings.general.flask_secret_key
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.config['JSON_AS_ASCII'] = False

    if args.dev:
        app.config["DEBUG"] = True
    else:
        app.config["DEBUG"] = False

    socketio.init_app(app, path=base_url.rstrip('/')+'/api/socket.io', cors_allowed_origins='*',
                      async_mode='threading', allow_upgrades=False, transports='polling')
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
