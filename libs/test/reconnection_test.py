import logging
import time
import uuid
import threading
from typing import Dict
from signalrcore.hub_connection_builder import HubConnectionBuilder
from signalrcore.hub.errors import HubConnectionError
from test.base_test_case import BaseTestCase
from signalrcore.transport.websockets.reconnection\
    import RawReconnectionHandler, IntervalReconnectionHandler


LOCKS: Dict[str, threading.Lock] = {}


class TestReconnectMethods(BaseTestCase):

    def test_reconnect_interval_config(self):
        connection = HubConnectionBuilder()\
            .with_url(self.server_url, options={"verify_ssl": False})\
            .configure_logging(logging.ERROR)\
            .with_automatic_reconnect({
                "type": "interval",
                "intervals": [1, 2, 4, 45, 6, 7, 8, 9, 10]
            })\
            .build()

        identifier = str(uuid.uuid4())
        LOCKS[identifier] = threading.Lock()

        def release():
            LOCKS[identifier].release()

        connection.on_open(release)
        connection.on_close(release)

        self.assertTrue(LOCKS[identifier].acquire(timeout=10))

        connection.start()

        self.assertTrue(LOCKS[identifier].acquire(timeout=10))

        connection.stop()

        self.assertTrue(LOCKS[identifier].acquire(timeout=10))

        del LOCKS[identifier]

    def test_reconnect_interval(self):
        connection = HubConnectionBuilder()\
            .with_url(self.server_url, options={"verify_ssl": False})\
            .configure_logging(logging.ERROR)\
            .with_automatic_reconnect({
                "type": "interval",
                "intervals": [1, 2, 4, 45, 6, 7, 8, 9, 10],
                "keep_alive_interval": 3
            })\
            .build()
        self.reconnect_test(connection)

    def test_no_reconnect(self):
        connection = HubConnectionBuilder()\
            .with_url(self.server_url, options={"verify_ssl": False})\
            .configure_logging(logging.ERROR)\
            .build()

        identifier = str(uuid.uuid4())
        LOCKS[identifier] = threading.Lock()

        def release(msg=None):
            LOCKS[identifier].release()

        LOCKS[identifier].acquire(timeout=10)

        connection.on_open(release)

        connection.on("ReceiveMessage", release)

        connection.start()

        self.assertTrue(LOCKS[identifier].acquire(timeout=10))
        # Released on ReOpen

        connection.send("DisconnectMe", [])

        self.assertTrue(LOCKS[identifier].acquire(timeout=10))

        time.sleep(10)

        self.assertRaises(
            HubConnectionError,
            lambda: connection.send("DisconnectMe", []))

        connection.stop()
        del LOCKS[identifier]

    def reconnect_test(self, connection):
        identifier = str(uuid.uuid4())
        LOCKS[identifier] = threading.Lock()

        def release():
            LOCKS[identifier].release()

        connection.on_open(release)
        connection.on_reconnect(release)

        self.assertTrue(LOCKS[identifier].acquire(timeout=10))

        connection.start()

        self.assertTrue(LOCKS[identifier].acquire(timeout=10))

        connection.on_open(lambda: None)

        # Release on Open
        connection.send("DisconnectMe", [])

        self.assertTrue(LOCKS[identifier].acquire(timeout=60))
        # released on reopen

        connection.stop()
        del LOCKS[identifier]

    def test_raw_reconnection(self):
        connection = HubConnectionBuilder()\
            .with_url(self.server_url, options={"verify_ssl": False})\
            .configure_logging(logging.DEBUG)\
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 10,
                "max_attempts": 4
            })\
            .build()

        self.reconnect_test(connection)

    def test_raw_handler(self):
        handler = RawReconnectionHandler(5, 10)
        attempt = 0

        while attempt <= 10:
            self.assertEqual(handler.next(), 5)
            attempt = attempt + 1

        self.assertRaises(ValueError, handler.next)

    def test_interval_handler(self):
        intervals = [1, 2, 4, 5, 6]
        handler = IntervalReconnectionHandler(intervals)
        for interval in intervals:
            self.assertEqual(handler.next(), interval)
        self.assertRaises(ValueError, handler.next)

    def tearDown(self):
        pass

    def setUp(self):
        pass
