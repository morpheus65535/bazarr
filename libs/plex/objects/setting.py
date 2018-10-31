from plex.objects.core.base import Descriptor, Property


class Setting(Descriptor):
    id = Property

    label = Property
    summary = Property

    type = Property
    group = Property

    value = Property(resolver=lambda: Setting.parse_value)
    default = Property(resolver=lambda: Setting.parse_default)
    options = Property('enumValues', resolver=lambda: Setting.parse_options)

    hidden = Property(type=[int, bool])
    advanced = Property(type=[int, bool])

    @classmethod
    def parse_value(cls, client, node):
        type = cls.helpers.get(node, 'type')
        value = cls.helpers.get(node, 'value')

        return ['value'], Setting.convert(type, value)

    @classmethod
    def parse_default(cls, client, node):
        type = cls.helpers.get(node, 'type')
        default = cls.helpers.get(node, 'default')

        return ['default'], Setting.convert(type, default)

    @classmethod
    def parse_options(cls, client, node):
        value = cls.helpers.get(node, 'enumValues')

        if not value:
            return [], None

        return ['enumValues'], [
            tuple(option.split(':', 2)) for option in value.split('|')
        ]

    @staticmethod
    def convert(type, value):
        if type == 'bool':
            value = value.lower()
            value = value == 'true'
        elif type == 'int':
            value = int(value)

        return value
