from plex.objects.core.base import Descriptor, Property, DescriptorMixin
from plex.objects.player import Player
from plex.objects.transcode_session import TranscodeSession
from plex.objects.user import User


class SessionMixin(DescriptorMixin):
    session = Property(resolver=lambda: SessionMixin.construct_session)

    @staticmethod
    def construct_session(client, node):
        return Session.construct(client, node, child=True)


class Session(Descriptor):
    key = Property('sessionKey', int)

    user = Property(resolver=lambda: Session.construct_user)
    player = Property(resolver=lambda: Session.construct_player)
    transcode_session = Property(resolver=lambda: Session.construct_transcode_session)

    @classmethod
    def construct_user(cls, client, node):
        return User.construct(client, cls.helpers.find(node, 'User'), child=True)

    @classmethod
    def construct_player(cls, client, node):
        return Player.construct(client, cls.helpers.find(node, 'Player'), child=True)

    @classmethod
    def construct_transcode_session(cls, client, node):
        return TranscodeSession.construct(client, cls.helpers.find(node, 'TranscodeSession'), child=True)
