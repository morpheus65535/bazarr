import json
import sys
from threading import Thread
from signalr.events import EventHook
from signalr.hubs import Hub
from signalr.transports import AutoTransport


class Connection:
    protocol_version = '1.5'

    def __init__(self, url, session):
        self.url = url
        self.__hubs = {}
        self.qs = {}
        self.__send_counter = -1
        self.token = None
        self.id = None
        self.data = None
        self.received = EventHook()
        self.error = EventHook()
        self.starting = EventHook()
        self.stopping = EventHook()
        self.exception = EventHook()
        self.is_open = False
        self.__transport = AutoTransport(session, self)
        self.__listener_thread = None
        self.started = False

        def handle_error(**kwargs):
            error = kwargs["E"] if "E" in kwargs else None
            if error is None:
                return

            self.error.fire(error)

        self.received += handle_error

        self.starting += self.__set_data

    def __set_data(self):
        self.data = json.dumps([{'name': hub_name} for hub_name in self.__hubs])

    def increment_send_counter(self):
        self.__send_counter += 1
        return self.__send_counter

    def start(self):
        self.starting.fire()

        negotiate_data = self.__transport.negotiate()
        self.token = negotiate_data['ConnectionToken']
        self.id = negotiate_data['ConnectionId']

        listener = self.__transport.start()

        def wrapped_listener():
            while self.is_open:
                try:
                    listener()
                except:
                    self.exception.fire(*sys.exc_info())
                    self.is_open = False

        self.is_open = True
        self.__listener_thread = Thread(target=wrapped_listener)
        self.__listener_thread.start()
        self.started = True

    def wait(self, timeout=30):
        Thread.join(self.__listener_thread, timeout)

    def send(self, data):
        self.__transport.send(data)

    def close(self):
        self.is_open = False
        self.__listener_thread.join()
        self.__transport.close()

    def register_hub(self, name):
        if name not in self.__hubs:
            if self.started:
                raise RuntimeError(
                    'Cannot create new hub because connection is already started.')

            self.__hubs[name] = Hub(name, self)
        return self.__hubs[name]

    def hub(self, name):
        return self.__hubs[name]

    def __enter__(self):
        self.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
