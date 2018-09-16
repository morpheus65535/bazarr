# -*- coding: utf-8 -*-
#
# Pushover Notify Wrapper
#
# Copyright (C) 2017-2018 Chris Caron <lead2gold@gmail.com>
#
# This file is part of apprise.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

import re
import requests

from ..utils import compat_is_basestring
from .NotifyBase import NotifyBase
from .NotifyBase import HTTP_ERROR_MAP

# Flag used as a placeholder to sending to all devices
PUSHOVER_SEND_TO_ALL = 'ALL_DEVICES'

# Used to validate API Key
VALIDATE_TOKEN = re.compile(r'^[a-z0-9]{30}$', re.I)

# Used to detect a User and/or Group
VALIDATE_USERGROUP = re.compile(r'^[a-z0-9]{30}$', re.I)

# Used to detect a User and/or Group
VALIDATE_DEVICE = re.compile(r'^[a-z0-9_]{1,25}$', re.I)


# Priorities
class PushoverPriority(object):
    LOW = -2
    MODERATE = -1
    NORMAL = 0
    HIGH = 1
    EMERGENCY = 2


PUSHOVER_PRIORITIES = (
    PushoverPriority.LOW,
    PushoverPriority.MODERATE,
    PushoverPriority.NORMAL,
    PushoverPriority.HIGH,
    PushoverPriority.EMERGENCY,
)

# Used to break path apart into list of devices
DEVICE_LIST_DELIM = re.compile(r'[ \t\r\n,\\/]+')

# Extend HTTP Error Messages
PUSHOVER_HTTP_ERROR_MAP = HTTP_ERROR_MAP.copy()
PUSHOVER_HTTP_ERROR_MAP.update({
    401: 'Unauthorized - Invalid Token.',
})


class NotifyPushover(NotifyBase):
    """
    A wrapper for Pushover Notifications
    """

    # All pushover requests are secure
    secure_protocol = 'pover'

    # Pushover uses the http protocol with JSON requests
    notify_url = 'https://api.pushover.net/1/messages.json'

    # The maximum allowable characters allowed in the body per message
    body_maxlen = 512

    def __init__(self, token, devices=None, priority=None, **kwargs):
        """
        Initialize Pushover Object
        """
        super(NotifyPushover, self).__init__(**kwargs)

        try:
            # The token associated with the account
            self.token = token.strip()

        except AttributeError:
            # Token was None
            self.logger.warning('No API Token was specified.')
            raise TypeError('No API Token was specified.')

        if not VALIDATE_TOKEN.match(self.token):
            self.logger.warning(
                'The API Token specified (%s) is invalid.' % token,
            )
            raise TypeError(
                'The API Token specified (%s) is invalid.' % token,
            )

        if compat_is_basestring(devices):
            self.devices = [x for x in filter(bool, DEVICE_LIST_DELIM.split(
                devices,
            ))]

        elif isinstance(devices, (set, tuple, list)):
            self.devices = devices

        else:
            self.devices = list()

        if len(self.devices) == 0:
            self.devices = (PUSHOVER_SEND_TO_ALL, )

        # The Priority of the message
        if priority not in PUSHOVER_PRIORITIES:
            self.priority = PushoverPriority.NORMAL

        else:
            self.priority = priority

        if not self.user:
            self.logger.warning('No user was specified.')
            raise TypeError('No user was specified.')

        if not VALIDATE_USERGROUP.match(self.user):
            self.logger.warning(
                'The user/group specified (%s) is invalid.' % self.user,
            )
            raise TypeError(
                'The user/group specified (%s) is invalid.' % self.user,
            )

    def notify(self, title, body, **kwargs):
        """
        Perform Pushover Notification
        """

        headers = {
            'User-Agent': self.app_id,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        auth = (self.token, '')

        # error tracking (used for function return)
        has_error = False

        # Create a copy of the devices list
        devices = list(self.devices)
        while len(devices):
            device = devices.pop(0)

            if VALIDATE_DEVICE.match(device) is None:
                self.logger.warning(
                    'The device specified (%s) is invalid.' % device,
                )
                has_error = True
                continue

            # prepare JSON Object
            payload = {
                'token': self.token,
                'user': self.user,
                'priority': str(self.priority),
                'title': title,
                'message': body,
                'device': device,
            }

            self.logger.debug('Pushover POST URL: %s (cert_verify=%r)' % (
                self.notify_url, self.verify_certificate,
            ))
            self.logger.debug('Pushover Payload: %s' % str(payload))
            try:
                r = requests.post(
                    self.notify_url,
                    data=payload,
                    headers=headers,
                    auth=auth,
                    verify=self.verify_certificate,
                )
                if r.status_code != requests.codes.ok:
                    # We had a problem
                    try:
                        self.logger.warning(
                            'Failed to send Pushover:%s '
                            'notification: %s (error=%s).' % (
                                device,
                                PUSHOVER_HTTP_ERROR_MAP[r.status_code],
                                r.status_code))

                    except KeyError:
                        self.logger.warning(
                            'Failed to send Pushover:%s '
                            'notification (error=%s).' % (
                                device,
                                r.status_code))

                    # self.logger.debug('Response Details: %s' % r.raw.read())

                    # Return; we're done
                    has_error = True

                else:
                    self.logger.info(
                        'Sent Pushover notification to %s.' % device)

            except requests.RequestException as e:
                self.logger.warning(
                    'A Connection error occured sending Pushover:%s ' % (
                        device) + 'notification.'
                )
                self.logger.debug('Socket Exception: %s' % str(e))
                has_error = True

            if len(devices):
                # Prevent thrashing requests
                self.throttle()

        return not has_error

    @staticmethod
    def parse_url(url):
        """
        Parses the URL and returns enough arguments that can allow
        us to substantiate this object.

        """
        results = NotifyBase.parse_url(url)

        if not results:
            # We're done early as we couldn't load the results
            return results

        # Apply our settings now
        devices = NotifyBase.unquote(results['fullpath'])

        if 'priority' in results['qsd'] and len(results['qsd']['priority']):
            _map = {
                'l': PushoverPriority.LOW,
                '-2': PushoverPriority.LOW,
                'm': PushoverPriority.MODERATE,
                '-1': PushoverPriority.MODERATE,
                'n': PushoverPriority.NORMAL,
                '0': PushoverPriority.NORMAL,
                'h': PushoverPriority.HIGH,
                '1': PushoverPriority.HIGH,
                'e': PushoverPriority.EMERGENCY,
                '2': PushoverPriority.EMERGENCY,
            }
            try:
                results['priority'] = \
                    _map[results['qsd']['priority'][0].lower()]

            except KeyError:
                # No priority was set
                pass

        results['token'] = results['host']
        results['devices'] = devices

        return results
