import os
import re
import unittest
import logging
import time
import uuid
import threading

from signalrcore.hub_connection_builder import HubConnectionBuilder
from signalrcore.hub.errors import HubError, HubConnectionError
from test.base_test_case import BaseTestCase, Urls

class TestSendException(BaseTestCase):
    def receive_message(self, _):
        raise Exception()

    def setUp(self):
        self.connection = self.get_connection()
        self.connection.start()
        while not self.connected:
            time.sleep(0.1)
    
    def test_send_exception(self):
        _lock = threading.Lock()
        _lock.acquire()
        self.connection.send("SendMessage", ["user", "msg"])
        del _lock

    def test_hub_error(self):
        _lock = threading.Lock()

        self.assertTrue(_lock.acquire(timeout=10))     
        self.connection.on_error(lambda _: _lock.release())

        def on_message(_):
            _lock.release()
            self.assertTrue(_lock.acquire(timeout=10)) 

        self.connection.on("ThrowExceptionCall", on_message)
        self.connection.send("ThrowException", ["msg"])

class TestSendExceptionMsgPack(TestSendException):
    def setUp(self):
        self.connection = self.get_connection(msgpack=True)
        self.connection.start()
        while not self.connected:
            time.sleep(0.1)
        
class TestSendWarning(BaseTestCase):
    def setUp(self):
        self.connection = self.get_connection()
        self.connection.start()
        while not self.connected:
            time.sleep(0.1)
    
    def test_send_warning(self):
        _lock = threading.Lock()
        _lock.acquire()
        self.connection.send("SendMessage", ["user", "msg"], lambda m: _lock.release())
        self.assertTrue(_lock.acquire(timeout=10))
        del _lock

class TestSendWarningMsgPack(TestSendWarning):
    def setUp(self):
        self.connection = super().get_connection(msgpack=True)
        self.connection.start()
        while not self.connected:
            time.sleep(0.1)
        

class TestSendMethod(BaseTestCase):
    received = False
    message = None
    def setUp(self):
        self.connection = self.get_connection()
        self.connection.on("ReceiveMessage", self.receive_message)
        self.connection.start()
        while not self.connected:
            time.sleep(0.1)

    def receive_message(self, args):
        self.assertEqual(args[1], self.message)
        self.received = True


    def test_send_bad_args(self):
        class A():
            pass

        self.assertRaises(TypeError, lambda : self.connection.send("SendMessage", A()))

    def test_send(self):
        self.message = "new message {0}".format(uuid.uuid4())
        self.username = "mandrewcito"
        self.received = False
        self.connection.send("SendMessage", [self.username, self.message])
        while not self.received:
            time.sleep(0.1)
        self.assertTrue(self.received)

    def test_send_with_callback(self):
        self.message = "new message {0}".format(uuid.uuid4())
        self.username = "mandrewcito"
        self.received = False
        _lock = threading.Lock()
        _lock.acquire()
        uid = str(uuid.uuid4())

        def release(m):
            self.assertTrue(m.invocation_id, uid)
            _lock.release()

        self.connection.send(
            "SendMessage",
            [self.username, self.message],
            release,
            invocation_id=uid)

        self.assertTrue(_lock.acquire(timeout=10))
        del _lock

class TestSendNoSslMethod(TestSendMethod):
    server_url = Urls.server_url_no_ssl

class TestSendMethodMsgPack(TestSendMethod):
    def setUp(self):
        self.connection = super().get_connection(msgpack=True)
        self.connection.on("ReceiveMessage", super().receive_message)
        self.connection.start()
        while not self.connected:
            time.sleep(0.1)

class TestSendNoSslMethodMsgPack(TestSendMethodMsgPack):
    server_url = Urls.server_url_no_ssl    

class TestSendErrorMethod(BaseTestCase):
    received = False
    message = None
    def setUp(self):
        self.connection = self.get_connection()
        self.connection.on("ReceiveMessage", self.receive_message)

    def receive_message(self, args):
        self.assertEqual(args[1], self.message)
        self.received = True


    def test_send_with_error(self):
        self.message = "new message {0}".format(uuid.uuid4())
        self.username = "mandrewcito"

        self.assertRaises(HubConnectionError,lambda : self.connection.send("SendMessage", [self.username, self.message]))
        
        self.connection.start()
        while not self.connected:
            time.sleep(0.1)

        self.received = False
        self.connection.send("SendMessage", [self.username, self.message])        
        t0 = time.time()
        while not self.received:
            time.sleep(0.1)
        self.assertTrue(self.received)


class TestSendErrorNoSslMethod(TestSendErrorMethod):
    server_url = Urls.server_url_no_ssl


class TestSendErrorMethodMsgPack(TestSendErrorMethod):
    def get_connection(self):
        return super().get_connection(msgpack=True)

class TestSendErrorNoSslMethodMsgPack(TestSendErrorNoSslMethod):
    def get_connection(self):
        return super().get_connection(msgpack=True)
