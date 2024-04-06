# coding=utf-8

import signal
import warnings
import logging
import errno
from literals import EXIT_INTERRUPT, EXIT_NORMAL, EXIT_PORT_ALREADY_IN_USE_ERROR
from utilities.central import restart_bazarr, stop_bazarr

from waitress.server import create_server
from time import sleep

from api import api_bp
from .ui import ui_bp
from .get_args import args
from .config import settings, base_url
from .database import close_database
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
        self.interrupted = False

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
                super(Server, self).__init__()
            elif error.errno == errno.EADDRINUSE:
                if self.port != '6767':
                    logging.exception("BAZARR cannot bind to specified TCP port, trying with default (6767)")
                    self.port = '6767'
                    self.connected = False
                    super(Server, self).__init__()
                else:
                    logging.exception("BAZARR cannot bind to default TCP port (6767) because it's already in use, "
                                      "exiting...")
                    self.shutdown(EXIT_PORT_ALREADY_IN_USE_ERROR)
            else:
                logging.exception("BAZARR cannot start because of unhandled exception.")
                self.shutdown()

    def interrupt_handler(self, signum, frame):
        # print('Server signal interrupt handler called with signal', signum)
        if not self.interrupted:
            # ignore user hammering Ctrl-C; we heard you the first time!
            self.interrupted = True
            self.shutdown(EXIT_INTERRUPT)

    def start(self):
        logging.info(f'BAZARR is started and waiting for request on http://{self.server.effective_host}:'
                     f'{self.server.effective_port}')
        signal.signal(signal.SIGINT, self.interrupt_handler)
        try:
            self.server.run()
        except (KeyboardInterrupt, SystemExit):
            self.shutdown()
        except Exception:
            pass

    def close_all(self):
        print(f"Closing database...")
        close_database()
        print(f"Closing webserver...")
        self.server.close()

    def shutdown(self, status=EXIT_NORMAL):
        self.close_all()
        stop_bazarr(status, False)

    def restart(self):
        self.close_all()
        restart_bazarr()


webserver = Server()
