# coding=utf-8

import struct
import binascii

from pyga.requests import Event, Page, Tracker, Session, Visitor, Config


def track_event(category=None, action=None, label=None, value=None, identifier=None, first_use=None, add=None,
                noninteraction=True):
    anonymousConfig = Config()
    anonymousConfig.anonimize_ip_address = True

    tracker = Tracker('UA-86466078-1', 'none', conf=anonymousConfig)
    visitor = Visitor()

    # convert the last 8 bytes of the machine identifier to an integer to get a "unique" user
    visitor.unique_id = struct.unpack("!I", binascii.unhexlify(identifier[32:]))[0]/2

    if add:
        # add visitor's ip address (will be anonymized)
        visitor.ip_address = add

    if first_use:
        visitor.first_visit_time = first_use

    session = Session()
    event = Event(category=category, action=action, label=label, value=value, noninteraction=noninteraction)
    path = u"/" + u"/".join([category, action, label])
    page = Page(path.lower())

    tracker.track_event(event, session, visitor)
    tracker.track_pageview(page, session, visitor)
