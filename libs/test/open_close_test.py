import logging
import threading
import uuid

from signalrcore.hub_connection_builder import HubConnectionBuilder
from test.base_test_case import BaseTestCase

LOCKS = {}


class TestOpenCloseMethods(BaseTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_start(self):
        connection = HubConnectionBuilder()\
            .with_url(self.server_url, options={"verify_ssl": False})\
            .configure_logging(logging.ERROR)\
            .build()

        identifier = str(uuid.uuid4())
        LOCKS[identifier] = threading.Lock()

        def release():
            LOCKS[identifier].release()

        self.assertTrue(LOCKS[identifier].acquire(timeout=30))

        connection.on_open(release)
        connection.on_close(release)

        result = connection.start()

        self.assertTrue(result)

        self.assertTrue(LOCKS[identifier].acquire(timeout=30))
        # Released on open

        result = connection.start()

        self.assertFalse(result)

        connection.stop()

        del LOCKS[identifier]
        del connection

    def test_open_close(self):
        connection = self.get_connection()

        identifier = str(uuid.uuid4())
        LOCKS[identifier] = threading.Lock()

        def release():
            LOCKS[identifier].release()

        connection.on_open(release)
        connection.on_close(release)

        self.assertTrue(LOCKS[identifier].acquire(timeout=30))

        connection.start()

        self.assertTrue(
            LOCKS[identifier].acquire(timeout=30),
            "on_open was not fired")

        connection.on_open(lambda: None)

        connection.stop()

        self.assertTrue(
            LOCKS[identifier].acquire(timeout=30),
            "on_close was not fired")

        del LOCKS[identifier]
        del connection
