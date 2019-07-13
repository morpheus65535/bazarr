from six.moves.urllib_parse import urlparse


class Proxy(object):
    def __init__(self, proxy_type, proxy_address, proxy_port, proxy_login, proxy_password):
        self.proxyType = proxy_type
        self.proxyAddress = proxy_address
        self.proxyPort = proxy_port
        self.proxyLogin = proxy_login
        self.proxyPassword = proxy_password

    def serialize(self):
        result = {'proxyType': self.proxyType,
                  'proxyAddress': self.proxyAddress,
                  'proxyPort': self.proxyPort}
        if self.proxyLogin or self.proxyPassword:
            result['proxyLogin'] = self.proxyLogin
            result['proxyPassword'] = self.proxyPassword
        return result

    @classmethod
    def parse_url(cls, url):
        parsed = urlparse(url)
        return cls(proxy_type=parsed.scheme,
                   proxy_address=parsed.hostname,
                   proxy_port=parsed.port,
                   proxy_login=parsed.username,
                   proxy_password=parsed.password)
