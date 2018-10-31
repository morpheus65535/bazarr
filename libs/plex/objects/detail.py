from plex.objects.core.base import Descriptor, Property
from plex.objects.container import Container


class Detail(Container):
    myplex = Property(resolver=lambda: Detail.construct_myplex)
    transcoder = Property(resolver=lambda: Detail.construct_transcoder)

    friendly_name = Property('friendlyName')

    machine_identifier = Property('machineIdentifier')
    version = Property

    platform = Property
    platform_version = Property('platformVersion')

    allow_camera_upload = Property('allowCameraUpload', [int, bool])
    allow_channel_access = Property('allowChannelAccess', [int, bool])
    allow_sync = Property('allowSync', [int, bool])

    certificate = Property(type=[int, bool])
    multiuser = Property(type=[int, bool])
    sync = Property(type=[int, bool])

    start_state = Property('startState')

    silverlight = Property('silverlightInstalled', [int, bool])
    soundflower = Property('soundflowerInstalled', [int, bool])
    flash = Property('flashInstalled', [int, bool])
    webkit = Property(type=[int, bool])

    cookie_parameters = Property('requestParametersInCookie', [int, bool])

    @staticmethod
    def construct_myplex(client, node):
        return MyPlexDetail.construct(client, node, child=True)

    @staticmethod
    def construct_transcoder(client, node):
        return TranscoderDetail.construct(client, node, child=True)


class MyPlexDetail(Descriptor):
    enabled = Property('myPlex', type=bool)

    username = Property('myPlexUsername')

    mapping_state = Property('myPlexMappingState')
    signin_state = Property('myPlexSigninState')

    subscription = Property('myPlexSubscription', [int, bool])


class TranscoderDetail(Descriptor):
    audio = Property('transcoderAudio', [int, bool])
    video = Property('transcoderVideo', [int, bool])

    video_bitrates = Property('transcoderVideoBitrates')
    video_qualities = Property('transcoderVideoQualities')
    video_resolutions = Property('transcoderVideoResolutions')

    active_video_sessions = Property('transcoderActiveVideoSessions', int)
