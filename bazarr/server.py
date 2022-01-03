# coding=utf-8

import warnings
import logging
import os
import io
from waitress.server import create_server

from get_args import args
from config import settings, base_url
from database import database

from app import create_app
app = create_app()

from api import api_bp_list  # noqa E402
for item in api_bp_list:
    app.register_blueprint(item, url_prefix=base_url.rstrip('/') + '/api')


class Server:
    def __init__(self):
        # Mute DeprecationWarning
        warnings.simplefilter("ignore", DeprecationWarning)
        # Mute Insecure HTTPS requests made to Sonarr and Radarr
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')
        # Mute Python3 BrokenPipeError
        warnings.simplefilter("ignore", BrokenPipeError)

        self.server = create_server(app,
                                    host=str(settings.general.ip),
                                    port=int(args.port) if args.port else int(settings.general.port),
                                    threads=100)

    def start(self):
        try:
            logging.info(
                'BAZARR is started and waiting for request on http://' + str(settings.general.ip) + ':' + (str(
                    args.port) if args.port else str(settings.general.port)) + str(base_url))
            self.server.run()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        try:
            self.server.close()
        except Exception as e:
            logging.error('BAZARR Cannot stop Waitress: ' + repr(e))
        else:
            database.close()
            try:
                stop_file = io.open(os.path.join(args.config_dir, "bazarr.stop"), "w", encoding='UTF-8')
            except Exception as e:
                logging.error('BAZARR Cannot create bazarr.stop file: ' + repr(e))
            else:
                logging.info('Bazarr is being shutdown...')
                stop_file.write(str(''))
                stop_file.close()
                os._exit(0)

    def restart(self):
        try:
            self.server.close()
        except Exception as e:
            logging.error('BAZARR Cannot stop Waitress: ' + repr(e))
        else:
            database.close()
            try:
                restart_file = io.open(os.path.join(args.config_dir, "bazarr.restart"), "w", encoding='UTF-8')
            except Exception as e:
                logging.error('BAZARR Cannot create bazarr.restart file: ' + repr(e))
            else:
                logging.info('Bazarr is being restarted...')
                restart_file.write(str(''))
                restart_file.close()
                os._exit(0)


webserver = Server()
