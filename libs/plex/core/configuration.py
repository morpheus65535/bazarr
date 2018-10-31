class ConfigurationManager(object):
    def __init__(self):
        self.stack = [
            Configuration(self)
        ]

    @property
    def current(self):
        return self.stack[-1]

    @property
    def defaults(self):
        return self.stack[0]

    def authentication(self, token):
        return Configuration(self).authentication(token)

    def cache(self, **definitions):
        return Configuration(self).cache(**definitions)

    def client(self, identifier, product, version):
        return Configuration(self).client(identifier, product, version)

    def device(self, name, system):
        return Configuration(self).device(name, system)

    def headers(self, headers):
        return Configuration(self).headers(headers)

    def platform(self, name, version):
        return Configuration(self).platform(name, version)

    def server(self, host='127.0.0.1', port=32400):
        return Configuration(self).server(host, port)

    def get(self, key, default=None):
        for x in range(len(self.stack) - 1, -1, -1):
            value = self.stack[x].get(key)

            if value is not None:
                return value

        return default

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.current[key] = value


class Configuration(object):
    def __init__(self, manager):
        self.manager = manager

        self.data = {}

    def authentication(self, token):
        self.data['authentication.token'] = token

        return self

    def cache(self, **definitions):
        for key, value in definitions.items():
            self.data['cache.%s' % key] = value

        return self

    def client(self, identifier, product, version):
        self.data['client.identifier'] = identifier

        self.data['client.product'] = product
        self.data['client.version'] = version

        return self

    def device(self, name, system):
        self.data['device.name'] = name
        self.data['device.system'] = system

        return self

    def headers(self, headers):
        self.data['headers'] = headers

        return self

    def platform(self, name, version):
        self.data['platform.name'] = name
        self.data['platform.version'] = version

        return self

    def server(self, host='127.0.0.1', port=32400):
        self.data['server.host'] = host
        self.data['server.port'] = port

        return self

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __enter__(self):
        self.manager.stack.append(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        item = self.manager.stack.pop()

        assert item == self

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
