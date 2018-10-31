from plex.objects.core.base import Descriptor, Property


class Server(Descriptor):
    name = Property
    host = Property

    address = Property
    port = Property(type=int)

    machine_identifier = Property('machineIdentifier')
    version = Property
