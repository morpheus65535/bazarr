from abc import abstractmethod
import json
import sys
import threading
if sys.version_info[0] < 3:
    from urllib import quote_plus
else:
    from urllib.parse import quote_plus



class Transport:
    def __init__(self, session, connection):
        self._session = session
        self._connection = connection

    @abstractmethod
    def _get_name(self):
        pass

    def negotiate(self):
        url = self.__get_base_url(self._connection,
                                  'negotiate',
                                  connectionData=self._connection.data)
        negotiate = self._session.get(url)

        negotiate.raise_for_status()

        return negotiate.json()

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def send(self, data):
        pass

    @abstractmethod
    def close(self):
        pass

    def accept(self, negotiate_data):
        return True

    def _handle_notification(self, message):
        if len(message) > 0:
            data = json.loads(message)
            self._connection.received.fire(**data)
        #thread.sleep() #TODO: investigate if we should sleep here

    def _get_url(self, action, **kwargs):
        args = kwargs.copy()
        args['transport'] = self._get_name()
        args['connectionToken'] = self._connection.token
        args['connectionData'] = self._connection.data

        return self.__get_base_url(self._connection, action, **args)

    @staticmethod
    def __get_base_url(connection, action, **kwargs):
        args = kwargs.copy()
        args.update(connection.qs)
        args['clientProtocol'] = connection.protocol_version
        query = '&'.join(['{key}={value}'.format(key=key, value=quote_plus(args[key])) for key in args])

        return '{url}/{action}?{query}'.format(url=connection.url,
                                               action=action,
                                               query=query)
