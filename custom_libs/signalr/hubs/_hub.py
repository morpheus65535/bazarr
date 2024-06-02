from signalr.events import EventHook


class Hub:
    def __init__(self, name, connection):
        self.name = name
        self.server = HubServer(name, connection, self)
        self.client = HubClient(name, connection)
        self.error = EventHook()


class HubServer:
    def __init__(self, name, connection, hub):
        self.name = name
        self.__connection = connection
        self.__hub = hub

    def invoke(self, method, *data):
        self.__connection.send({
            'H': self.name,
            'M': method,
            'A': data,
            'I': self.__connection.increment_send_counter()
        })


class HubClient(object):
    def __init__(self, name, connection):
        self.name = name
        self.__handlers = {}

        def handle(**kwargs):
            messages = kwargs['M'] if 'M' in kwargs and len(kwargs['M']) > 0 else {}
            for inner_data in messages:
                hub = inner_data['H'] if 'H' in inner_data else ''
                if hub.lower() == self.name.lower():
                    method = inner_data['name']
                    if method in self.__handlers:
                        self.__handlers[method].fire(inner_data)

        connection.received += handle

    def on(self, method, handler):
        if method not in self.__handlers:
            self.__handlers[method] = EventHook()
        self.__handlers[method] += handler

    def off(self, method, handler):
        if method in self.__handlers:
            self.__handlers[method] -= handler


class DictToObj:
    def __init__(self, d):
        self.__dict__ = d
