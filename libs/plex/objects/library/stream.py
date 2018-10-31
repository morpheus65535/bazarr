from plex.objects.core.base import Descriptor, Property


class Stream(Descriptor):
    id = Property(type=int)
    index = Property(type=int)

    stream_key = Property('key')

    stream_type = Property('streamType', type=int)
    selected = Property(type=bool)

    forced = Property(type=bool)
    default = Property(type=bool)

    title = Property
    duration = Property(type=int)

    codec = Property
    codec_id = Property('codecID')

    bit_depth = Property('bitDepth', type=int)
    chroma_subsampling = Property('chromaSubsampling')
    color_space = Property('colorSpace')

    width = Property(type=int)
    height = Property(type=int)

    bitrate = Property(type=int)
    bitrate_mode = Property('bitrateMode')

    channels = Property(type=int)
    sampling_rate = Property('samplingRate', type=int)

    frame_rate = Property('frameRate')
    profile = Property
    scan_type = Property('scanType')

    language = Property('language')
    language_code = Property('languageCode')

    bvop = Property(type=int)
    gmc = Property(type=int)
    level = Property(type=int)
    qpel = Property(type=int)

    @classmethod
    def from_node(cls, client, node):
        items = []

        for genre in cls.helpers.findall(node, 'Stream'):
            _, obj = Stream.construct(client, genre, child=True)

            items.append(obj)

        return [], items
