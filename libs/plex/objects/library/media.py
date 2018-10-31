from plex.objects.core.base import Descriptor, Property
from plex.objects.library.part import Part


class Media(Descriptor):
    parts = Property(resolver=lambda: Part.from_node)

    id = Property(type=int)

    video_codec = Property('videoCodec')
    video_frame_rate = Property('videoFrameRate')
    video_resolution = Property('videoResolution')

    audio_channels = Property('audioChannels', type=int)
    audio_codec = Property('audioCodec')

    container = Property

    width = Property(type=int)
    height = Property(type=int)

    aspect_ratio = Property('aspectRatio', type=float)
    bitrate = Property(type=int)
    duration = Property(type=int)

    #@classmethod
    #def from_node(cls, client, node):
    #    return cls.construct(client, cls.helpers.find(node, 'Media'), child=True)

    @classmethod
    def from_node(cls, client, node):
        items = []

        for genre in cls.helpers.findall(node, 'Media'):
            _, obj = Media.construct(client, genre, child=True)

            items.append(obj)

        return [], items
