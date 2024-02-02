import unittest
import logging
import time
from signalrcore.hub_connection_builder import HubConnectionBuilder
from signalrcore.protocol.messagepack_protocol import MessagePackHubProtocol
class Urls:
    server_url_no_ssl = "ws://localhost:5000/chatHub"
    server_url_ssl = "wss://localhost:5001/chatHub"
    server_url_no_ssl_auth = "ws://localhost:5000/authHub"
    server_url_ssl_auth = "wss://localhost:5001/authHub"
    login_url_ssl =  "https://localhost:5001/users/authenticate"
    login_url_no_ssl =  "http://localhost:5000/users/authenticate"

class InternalTestCase(unittest.TestCase):
    connection = None
    connected = False
    def get_connection(self):
        raise NotImplementedError()

    def setUp(self):
        self.connection = self.get_connection()
        self.connection.start()
        t0 = time.time()
        while not self.connected:
            time.sleep(0.1)
            if time.time() - t0 > 20:
                raise ValueError("TIMEOUT ")

    def tearDown(self):
        self.connection.stop()

    def on_open(self):
        self.connected = True

    def on_close(self):
        self.connected = False

class BaseTestCase(InternalTestCase):
    server_url = Urls.server_url_ssl

    def get_connection(self, msgpack=False):
        builder = HubConnectionBuilder()\
            .with_url(self.server_url, options={"verify_ssl":False})\
            .configure_logging(logging.ERROR)\
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "reconnect_interval": 5,
                "max_attempts": 5
            })

        if msgpack:
            builder.with_hub_protocol(MessagePackHubProtocol())

        hub = builder.build()
        hub.on_open(self.on_open)
        hub.on_close(self.on_close)
        return hub