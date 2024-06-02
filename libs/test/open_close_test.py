import os
import unittest
import logging
import time
import threading
import uuid

from subprocess import Popen, PIPE
from signalrcore.hub_connection_builder import HubConnectionBuilder
from signalrcore.subject import Subject
from test.base_test_case import BaseTestCase, Urls

class TestClientStreamMethod(BaseTestCase):    
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_start(self):
        connection = HubConnectionBuilder()\
            .with_url(self.server_url, options={"verify_ssl": False})\
            .configure_logging(logging.ERROR)\
            .build()
        
        _lock = threading.Lock()
        self.assertTrue(_lock.acquire(timeout=30))
        

        connection.on_open(lambda: _lock.release())
        connection.on_close(lambda: _lock.release())
        
        result = connection.start()

        self.assertTrue(result)
        
        self.assertTrue(_lock.acquire(timeout=30))  # Released on open
        
        result = connection.start()

        self.assertFalse(result)

        connection.stop()

    def test_open_close(self):
        self.connection = self.get_connection()
      
        _lock = threading.Lock()

        self.connection.on_open(lambda: _lock.release())
        self.connection.on_close(lambda: _lock.release())

        self.assertTrue(_lock.acquire())

        self.connection.start()

        self.assertTrue(_lock.acquire())
        
        self.connection.stop()
        
        self.assertTrue(_lock.acquire())

        _lock.release()
        del _lock