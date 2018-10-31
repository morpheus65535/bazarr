from plex.interfaces.core.base import Interface


class ChannelInterface(Interface):
    path = 'channels'

    def all(self):
        raise NotImplementedError()
