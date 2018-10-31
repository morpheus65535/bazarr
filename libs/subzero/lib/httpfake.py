# coding=utf-8


class PlexPyNativeResponseProxy(object):
    """
    The equally stupid counterpart to Sub-Zero.support.lib.PlexPyNativeRequestProxy.
    Incompletely mimics a requests response object for the plex.py library to use.
    """
    data = None
    headers = None
    response_code = None
    request = None

    def __init__(self, response, status_code, request):
        if response:
            self.data = response.content
            self.headers = response.headers
        self.response_code = status_code
        self.request = request

    def content(self):
        return self.data

    content = property(content)

    def status_code(self):
        return self.response_code

    status_code = property(status_code)

    def url(self):
        return self.request.url

    url = property(url)

    def __str__(self):
        return str(self.data)

    def __unicode__(self):
        return unicode(self.data)

    def __repr__(self):
        return repr(self.data)


