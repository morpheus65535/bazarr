# coding=utf-8

import warnings
import logging
import os
import io
import errno

from waitress.server import create_server
from time import sleep
from sqlalchemy.orm import close_all_sessions

from api import api_bp
from .ui import ui_bp
from .get_args import args
from .config import settings, base_url
from .database import database
from .app import create_app

app = create_app()
ui_bp.register_blueprint(api_bp, url_prefix='/api')
# Mute UserWarning with flask-restx and Flask >= 2.2.0. Will be raised as an exception in 2.3.0
# https://github.com/python-restx/flask-restx/issues/485
warnings.filterwarnings('ignore', message='The setup method ')
app.register_blueprint(ui_bp, url_prefix=base_url.rstrip('/'))


class Server:
    def __init__(self):
        # Mute DeprecationWarning
        warnings.simplefilter("ignore", DeprecationWarning)
        # Mute Insecure HTTPS requests made to Sonarr and Radarr
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')
        # Mute Python3 BrokenPipeError
        warnings.simplefilter("ignore", BrokenPipeError)

        self.server = None
        self.connected = False
        self.address = str(settings.general.ip)
        self.port = int(args.port) if args.port else int(settings.general.port)

        while not self.connected:
            sleep(0.1)
            self.configure_server()

    def configure_server(self):
        try:
            self.server = create_server(app,
                                        host=self.address,
                                        port=self.port,
                                        threads=100)
            self.connected = True
        except OSError as error:
            if error.errno == errno.EADDRNOTAVAIL:
                logging.exception("BAZARR cannot bind to specified IP, trying with default (0.0.0.0)")
                self.address = '0.0.0.0'
                self.connected = False
            elif error.errno == errno.EADDRINUSE:
                logging.exception("BAZARR cannot bind to specified TCP port, trying with default (6767)")
                self.port = '6767'
                self.connected = False
            else:
                logging.exception("BAZARR cannot start because of unhandled exception.")
                self.shutdown()

    def start(self):
        logging.info(f'BAZARR is started and waiting for request on http://{self.server.effective_host}:'
                     f'{self.server.effective_port}')
        try:
            self.server.run()
        except (KeyboardInterrupt, SystemExit):
            self.shutdown()
        except Exception:
            pass

    def shutdown(self):
        try:
            self.server.close()
        except Exception as e:
            logging.error(f'BAZARR Cannot stop Waitress: {repr(e)}')
        else:
            close_all_sessions()
            try:
                stop_file = io.open(os.path.join(args.config_dir, "bazarr.stop"), "w", encoding='UTF-8')
            except Exception as e:
                logging.error(f'BAZARR Cannot create stop file: {repr(e)}')
            else:
                logging.info('Bazarr is being shutdown...')
                stop_file.write(str(''))
                stop_file.close()
                os._exit(0)

    def restart(self):
        try:
            self.server.close()
        except Exception as e:
            logging.error(f'BAZARR Cannot stop Waitress: {repr(e)}')
        else:
            close_all_sessions()
            try:
                restart_file = io.open(os.path.join(args.config_dir, "bazarr.restart"), "w", encoding='UTF-8')
            except Exception as e:
                logging.error(f'BAZARR Cannot create restart file: {repr(e)}')
            else:
                logging.info('Bazarr is being restarted...')
                restart_file.write(str(''))
                restart_file.close()
                os._exit(0)


webserver = Server()
