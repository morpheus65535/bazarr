import os
import unittest
import threading
import logging
import time
import uuid
import requests
from signalrcore.hub_connection_builder import HubConnectionBuilder
from signalrcore.protocol.messagepack_protocol import MessagePackHubProtocol
from test.base_test_case import BaseTestCase, Urls

class TestSendAuthMethod(BaseTestCase):
    server_url = Urls.server_url_ssl_auth
    login_url = Urls.login_url_ssl
    email = "test"
    password = "test"
    received = False
    message = None
    _lock = None

    def login(self):
        response = requests.post(
            self.login_url,
            json={
                "username": self.email,
                "password": self.password
                },verify=False)
        return response.json()["token"]

    def _setUp(self, msgpack= False):
        builder = HubConnectionBuilder()\
            .with_url(self.server_url,
            options={
                "verify_ssl": False,
                "access_token_factory": self.login,
                "headers": {
                    "mycustomheader": "mycustomheadervalue"
                }
            })

        if msgpack:
            builder.with_hub_protocol(MessagePackHubProtocol())

        builder.configure_logging(logging.WARNING)\
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "reconnect_interval": 5,
                "max_attempts": 5
            })
        self.connection = builder.build()
        self.connection.on("ReceiveMessage", self.receive_message)
        self.connection.on_open(self.on_open)
        self.connection.on_close(self.on_close)
        self._lock = threading.Lock()
        self.assertTrue(self._lock.acquire(timeout=30))
        self.connection.start()
    
    def on_open(self):
        self._lock.release()

    def setUp(self):
        self._setUp()

    def receive_message(self, args):
        self._lock.release()
        self.assertEqual(args[0], self.message)
        
    def test_send(self):
        self.message = "new message {0}".format(uuid.uuid4())
        self.username = "mandrewcito"
        self.assertTrue(self._lock.acquire(timeout=30))
        self.connection.send("SendMessage", [self.message])
        self.assertTrue(self._lock.acquire(timeout=30))
        del self._lock    
        
class TestSendNoSslAuthMethod(TestSendAuthMethod):
    server_url = Urls.server_url_no_ssl_auth
    login_url = Urls.login_url_no_ssl

class TestSendAuthMethodMsgPack(TestSendAuthMethod):
    def setUp(self):
        self._setUp(msgpack=True)

class TestSendNoSslAuthMethodMsgPack(TestSendAuthMethod):
    server_url = Urls.server_url_no_ssl_auth
    login_url = Urls.login_url_no_ssl