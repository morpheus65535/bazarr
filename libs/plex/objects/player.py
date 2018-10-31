from plex.objects.core.base import Descriptor, Property


class Player(Descriptor):
    title = Property
    machine_identifier = Property('machineIdentifier')

    state = Property

    platform = Property
    product = Property
