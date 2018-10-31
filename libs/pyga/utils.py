# -*- coding: utf-8 -*-

import logging
from random import randint
import re
import six
import os
from datetime import datetime

__author__ = "Arun KR (kra3) <the1.arun@gmail.com>"
__license__ = "Simplified BSD"

RE_IP = re.compile(r'^[\d+]{1,3}\.[\d+]{1,3}\.[\d+]{1,3}\.[\d+]{1,3}$', re.I)
RE_PRIV_IP = re.compile(r'^(?:127\.0\.0\.1|10\.|192\.168\.|172\.(?:1[6-9]|2[0-9]|3[0-1])\.)')
RE_LOCALE = re.compile(r'(^|\s*,\s*)([a-zA-Z]{1,8}(-[a-zA-Z]{1,8})*)\s*(;\s*q\s*=\s*(1(\.0{0,3})?|0(\.[0-9]{0,3})))?', re.I)
RE_GA_ACCOUNT_ID = re.compile(r'^(UA|MO)-[0-9]*-[0-9]*$')
RE_FIRST_THREE_OCTETS_OF_IP = re.compile(r'^((\d{1,3}\.){3})\d{1,3}$')

def convert_ga_timestamp(timestamp_string):
    timestamp = float(timestamp_string)
    if timestamp > ((2 ** 31) - 1):
        timestamp /= 1000
    return datetime.utcfromtimestamp(timestamp)

def get_32bit_random_num():
    return randint(0, 0x7fffffff)

def is_valid_ip(ip):
    return True if RE_IP.match(str(ip)) else False

def is_private_ip(ip):
    return True if RE_PRIV_IP.match(str(ip)) else False

def validate_locale(locale):
    return RE_LOCALE.findall(str(locale))

def is_valid_google_account(account):
    return True if RE_GA_ACCOUNT_ID.match(str(account)) else False

def generate_hash(tmpstr):
    hash_val = 1

    if tmpstr:
        hash_val = 0
        for ordinal in map(ord, tmpstr[::-1]):
            hash_val = ((hash_val << 6) & 0xfffffff) + ordinal + (ordinal << 14)
            left_most_7 = hash_val & 0xfe00000
            if left_most_7 != 0:
                hash_val ^= left_most_7 >> 21

    return hash_val

def anonymize_ip(ip):
    if ip:
        match = RE_FIRST_THREE_OCTETS_OF_IP.findall(str(ip))
        if match:
            return '%s%s' % (match[0][0], '0')

    return ''

def encode_uri_components(value):
    '''Mimics Javascript's encodeURIComponent() function for consistency with the GA Javascript client.'''
    return convert_to_uri_component_encoding(six.moves.urllib.parse.quote(value))

def convert_to_uri_component_encoding(value):
    return value.replace('%21', '!').replace('%2A', '*').replace('%27', "'").replace('%28', '(').replace('%29', ')')

# Taken from expicient.com BJs repo.
def stringify(s, stype=None, fn=None):
    ''' Converts elements of a complex data structure to strings

    The data structure can be a multi-tiered one - with tuples and lists etc
    This method will loop through each and convert everything to string.
    For example - it can be -
    [[{'a1': {'a2': {'a3': ('a4', timedelta(0, 563)), 'a5': {'a6': datetime()}}}}]]
    which will be converted to -
    [[{'a1': {'a2': {'a3': ('a4', '0:09:23'), 'a5': {'a6': '2009-05-27 16:19:52.401500' }}}}]]

    @param stype: If only one type of data element needs to be converted to
        string without affecting others, stype can be used.
        In the earlier example, if it is called with stringify(s, stype=datetime.timedelta)
        the result would be
        [[{'a1': {'a2': {'a3': ('a4', '0:09:23'), 'a5': {'a6': datetime() }}}}]]

    Also, even though the name is stringify, any function can be run on it, based on
    parameter fn. If fn is None, it will be stringified.

    '''

    if type(s) in [list, set, dict, tuple]:
        if isinstance(s, dict):
            for k in s:
                s[k] = stringify(s[k], stype, fn)
        elif type(s) in [list, set]:
            for i, k in enumerate(s):
                s[i] = stringify(k, stype, fn)
        else: #tuple
            tmp = []
            for k in s:
                tmp.append(stringify(k, stype, fn))
            s = tuple(tmp)
    else:
        if fn:
            if not stype or (stype == type(s)):
                return fn(s)
        else:
            # To do str(s). But, str() can fail on unicode. So, use .encode instead
            if not stype or (stype == type(s)):
                try:
                    return six.text_type(s)
                    #return s.encode('ascii', 'replace')
                except AttributeError:
                    return str(s)
                except UnicodeDecodeError:
                    return s.decode('ascii', 'replace')
    return s
