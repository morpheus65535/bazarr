# -*- coding: utf-8 -*-
from datetime import time


class Component(object):
    """Base class for cue text.

    :param list components: sub-components of this one.

    """
    tag_name = 'Component'

    def __init__(self, components=None):
        if components is None:
            self.components = []
        elif isinstance(components, list):
            self.components = components
        else:
            self.components = [components]

    def __iter__(self):
        return iter(self.components)

    def __len__(self):
        return len(self.components)

    def __str__(self):
        return ''.join(str(c) for c in self.components)

    def __repr__(self):
        return '<{name}>{components}</{name}>'.format(name=self.tag_name,
                                                      components=''.join(repr(c) for c in self.components))


class Bold(Component):
    """Bold :class:`Component`."""
    tag_name = 'b'


class Italic(Component):
    """Italic :class:`Component`."""
    tag_name = 'i'


class Underline(Component):
    """Underline :class:`Component`."""
    tag_name = 'u'


class Strikethrough(Component):
    """Strikethrough :class:`Component`."""
    tag_name = 's'


class Font(Component):
    """Font :class:`Component`."""
    tag_name = 'font'

    def __init__(self, color, *args, **kwargs):
        super(Font, self).__init__(*args, **kwargs)
        self.color = color

    def __repr__(self):
        return '<{name} "{color}">{components}</{name}>'.format(name=self.tag_name, color=self.color,
                                                                components=''.join(repr(c) for c in self.components))


class Cue(object):
    """A single subtitle cue with timings and components.

    :param datetime.time start_time: start time.
    :param datetime.time end_time: end time.
    :param list components: cue components.

    """
    def __init__(self, start_time, end_time, components):
        self.start_time = start_time
        self.end_time = end_time
        self.components = components

    def __repr__(self):
        return '<Cue [{start_time}->{end_time}] "{text}">'.format(start_time=self.start_time, end_time=self.end_time,
                                                                  text=''.join(repr(c) for c in self.components))


if __name__ == '__main__':
    cue = Cue(time(), time(1), [Bold('Hello')])
    print repr(cue)
