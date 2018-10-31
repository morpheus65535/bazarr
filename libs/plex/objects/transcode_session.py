from plex.objects.core.base import Descriptor, Property


class TranscodeSession(Descriptor):
    key = Property

    progress = Property(type=float)
    speed = Property(type=float)
    duration = Property(type=int)

    protocol = Property
    throttled = Property(type=int)  # TODO this needs to cast: str -> int -> bool

    container = Property('container')

    video_codec = Property('videoCodec')
    video_decision = Property('videoDecision')

    audio_codec = Property('audioCodec')
    audio_channels = Property('audioChannels', int)
    audio_decision = Property('audioDecision')

    width = Property(type=int)
    height = Property(type=int)
