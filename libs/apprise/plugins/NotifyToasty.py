# -*- coding: utf-8 -*-
#
# (Super) Toasty Notify Wrapper
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

from .NotifyBase import NotifyBase
from .NotifyBase import HTTP_ERROR_MAP
from ..common import NotifyImageSize
from ..utils import compat_is_basestring

# Used to break apart list of potential devices by their delimiter
# into a usable list.
DEVICES_LIST_DELIM = re.compile(r'[ \t\r\n,\\/]+')


class NotifyToasty(NotifyBase):
    """
    A wrapper for Toasty Notifications
    """

    # The default protocol
    protocol = 'toasty'

    # Toasty uses the http protocol with JSON requests
    notify_url = 'http://api.supertoasty.com/notify/'

    # Allows the user to specify the NotifyImageSize object
    image_size = NotifyImageSize.XY_128

    def __init__(self, devices, **kwargs):
        """
        Initialize Toasty Object
        """
        super(NotifyToasty, self).__init__(**kwargs)

        if compat_is_basestring(devices):
            self.devices = [x for x in filter(bool, DEVICES_LIST_DELIM.split(
                devices,
            ))]

        elif isinstance(devices, (set, tuple, list)):
            self.devices = devices

        else:
            self.devices = list()

        if len(devices) == 0:
            raise TypeError('You must specify at least 1 device.')

        if not self.user:
            raise TypeError('You must specify a username.')

    def notify(self, title, body, notify_type, **kwargs):
        """
        Perform Toasty Notification
        """

        headers = {
            'User-Agent': self.app_id,
            'Content-Type': 'multipart/form-data',
        }

        # error tracking (used for function return)
        has_error = False

        # Create a copy of the devices list
        devices = list(self.devices)
        while len(devices):
            device = devices.pop(0)

            # prepare JSON Object
            payload = {
                'sender': NotifyBase.quote(self.user),
                'title': NotifyBase.quote(title),
                'text': NotifyBase.quote(body),
            }

            image_url = self.image_url(notify_type)
            if image_url:
                payload['image'] = image_url

            # URL to transmit content via
            url = '%s%s' % (self.notify_url, device)

            self.logger.debug('Toasty POST URL: %s (cert_verify=%r)' % (
                url, self.verify_certificate,
            ))
            self.logger.debug('Toasty Payload: %s' % str(payload))
            try:
                r = requests.get(
                    url,
                    data=payload,
                    headers=headers,
                    verify=self.verify_certificate,
                )
                if r.status_code != requests.codes.ok:
                    # We had a problem
                    try:
                        self.logger.warning(
                            'Failed to send Toasty:%s '
                            'notification: %s (error=%s).' % (
                                device,
                                HTTP_ERROR_MAP[r.status_code],
                                r.status_code))

                    except KeyError:
                        self.logger.warning(
                            'Failed to send Toasty:%s '
                            'notification (error=%s).' % (
                                device,
                                r.status_code))

                    # self.logger.debug('Response Details: %s' % r.raw.read())

                    # Return; we're done
                    has_error = True

                else:
                    self.logger.info(
                        'Sent Toasty notification to %s.' % device)

            except requests.RequestException as e:
                self.logger.warning(
                    'A Connection error occured sending Toasty:%s ' % (
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

        # Store our devices
        results['devices'] = '%s/%s' % (results['host'], devices)

        return results
