# -*- coding: utf-8 -*-

from datetime import datetime
from operator import itemgetter
from pyga import utils
from pyga import exceptions
try:
    from urlparse import urlparse
    from urllib import unquote_plus
except ImportError as e:
    from urllib.parse import urlparse
    from urllib.parse import unquote_plus


__author__ = "Arun KR (kra3) <the1.arun@gmail.com>"
__license__ = "Simplified BSD"


class Campaign(object):
    '''
    A representation of Campaign

    Properties:
    _type -- See TYPE_* constants, will be mapped to "__utmz" parameter.
    creation_time --  Time of the creation of this campaign, will be mapped to "__utmz" parameter.
    response_count -- Response Count, will be mapped to "__utmz" parameter.
        Is also used to determine whether the campaign is new or repeated,
        which will be mapped to "utmcn" and "utmcr" parameters.
    id -- Campaign ID, a.k.a. "utm_id" query parameter for ga.js
           Will be mapped to "__utmz" parameter.
    source -- Source, a.k.a. "utm_source" query parameter for ga.js.
              Will be mapped to "utmcsr" key in "__utmz" parameter.
    g_click_id -- Google AdWords Click ID, a.k.a. "gclid" query parameter for ga.js.
                  Will be mapped to "utmgclid" key in "__utmz" parameter.
    d_click_id -- DoubleClick (?) Click ID. Will be mapped to "utmdclid" key in "__utmz" parameter.
    name --  Name, a.k.a. "utm_campaign" query parameter for ga.js.
             Will be mapped to "utmccn" key in "__utmz" parameter.
    medium -- Medium, a.k.a. "utm_medium" query parameter for ga.js.
              Will be mapped to "utmcmd" key in "__utmz" parameter.
    term -- Terms/Keywords, a.k.a. "utm_term" query parameter for ga.js.
            Will be mapped to "utmctr" key in "__utmz" parameter.
    content -- Ad Content Description, a.k.a. "utm_content" query parameter for ga.js.
               Will be mapped to "utmcct" key in "__utmz" parameter.

    '''

    TYPE_DIRECT = 'direct'
    TYPE_ORGANIC = 'organic'
    TYPE_REFERRAL = 'referral'

    CAMPAIGN_DELIMITER = '|'

    UTMZ_PARAM_MAP = {
        'utmcid': 'id',
        'utmcsr': 'source',
        'utmgclid': 'g_click_id',
        'utmdclid': 'd_click_id',
        'utmccn': 'name',
        'utmcmd': 'medium',
        'utmctr': 'term',
        'utmcct': 'content',
    }

    def __init__(self, typ):
        self._type = None
        self.creation_time = None
        self.response_count = 0
        self.id = None
        self.source = None
        self.g_click_id = None
        self.d_click_id = None
        self.name = None
        self.medium = None
        self.term = None
        self.content = None

        if typ:
            if typ not in ('direct', 'organic', 'referral'):
                raise ValueError('Campaign type has to be one of the Campaign::TYPE_* constant values.')

            self._type = typ
            if typ == Campaign.TYPE_DIRECT:
                self.name = '(direct)'
                self.source = '(direct)'
                self.medium = '(none)'
            elif typ == Campaign.TYPE_REFERRAL:
                self.name = '(referral)'
                self.medium = 'referral'
            elif typ == Campaign.TYPE_ORGANIC:
                self.name = '(organic)'
                self.medium = 'organic'
            else:
                self._type = None

        self.creation_time = datetime.utcnow()

    def validate(self):
        if not self.source:
            raise exceptions.ValidationError('Campaigns need to have at least the "source" attribute defined.')

    @staticmethod
    def create_from_referrer(url):
        obj = Campaign(Campaign.TYPE_REFERRAL)
        parse_rslt = urlparse(url)
        obj.source = parse_rslt.netloc
        obj.content = parse_rslt.path
        return obj

    def extract_from_utmz(self, utmz):
        parts = utmz.split('.', 4)

        if len(parts) != 5:
            raise ValueError('The given "__utmz" cookie value is invalid.')

        self.creation_time = utils.convert_ga_timestamp(parts[1])
        self.response_count = int(parts[3])
        params = parts[4].split(Campaign.CAMPAIGN_DELIMITER)

        for param in params:
            key, val = param.split('=')

            try:
                setattr(self, self.UTMZ_PARAM_MAP[key], unquote_plus(val))
            except KeyError:
                continue

        return self


class CustomVariable(object):
    '''
    Represent a Custom Variable

    Properties:
    index -- Is the slot, you have 5 slots
    name -- Name given to custom variable
    value -- Value for the variable
    scope -- Scope can be any one of 1, 2 or 3.

    WATCH OUT: It's a known issue that GA will not decode URL-encoded
    characters in custom variable names and values properly, so spaces
    will show up as "%20" in the interface etc. (applicable to name & value)
    http://www.google.com/support/forum/p/Google%20Analytics/thread?tid=2cdb3ec0be32e078

    '''

    SCOPE_VISITOR = 1
    SCOPE_SESSION = 2
    SCOPE_PAGE = 3

    def __init__(self, index=None, name=None, value=None, scope=3):
        self.index = index
        self.name = name
        self.value = value
        self.scope = CustomVariable.SCOPE_PAGE
        if scope:
            self.scope = scope

    def __setattr__(self, name, value):
        if name == 'scope':
            if value and value not in range(1, 4):
                raise ValueError('Custom Variable scope has to be one of the 1,2 or 3')

        if name == 'index':
            # Custom Variables are limited to five slots officially, but there seems to be a
            # trick to allow for more of them which we could investigate at a later time (see
            # http://analyticsimpact.com/2010/05/24/get-more-than-5-custom-variables-in-google-analytics/
            if value and (value < 0 or value > 5):
                raise ValueError('Custom Variable index has to be between 1 and 5.')

        object.__setattr__(self, name, value)

    def validate(self):
        '''
        According to the GA documentation, there is a limit to the combined size of
        name and value of 64 bytes after URL encoding,
        see http://code.google.com/apis/analytics/docs/tracking/gaTrackingCustomVariables.html#varTypes
        and http://xahlee.org/js/google_analytics_tracker_2010-07-01_expanded.js line 563
        This limit was increased to 128 bytes BEFORE encoding with the 2012-01 release of ga.js however,
        see http://code.google.com/apis/analytics/community/gajs_changelog.html
        '''
        if len('%s%s' % (self.name, self.value)) > 128:
            raise exceptions.ValidationError('Custom Variable combined name and value length must not be larger than 128 bytes.')


class Event(object):
    '''
    Represents an Event
    https://developers.google.com/analytics/devguides/collection/gajs/eventTrackerGuide

    Properties:
    category -- The general event category
    action -- The action for the event
    label -- An optional descriptor for the event
    value -- An optional value associated with the event. You can see your
             event values in the Overview, Categories, and Actions reports,
             where they are listed by event or aggregated across events,
             depending upon your report view.
    noninteraction -- By default, event hits will impact a visitor's bounce rate.
                      By setting this parameter to true, this event hit
                      will not be used in bounce rate calculations.
                      (default False)
    '''

    def __init__(self, category=None, action=None, label=None, value=None, noninteraction=False):
        self.category = category
        self.action = action
        self.label = label
        self.value = value
        self.noninteraction = bool(noninteraction)

        if self.noninteraction and not self.value:
            self.value = 0

    def validate(self):
        if not(self.category and self.action):
            raise exceptions.ValidationError('Events, at least need to have a category and action defined.')


class Item(object):
    '''
    Represents an Item in Transaction

    Properties:
    order_id -- Order ID, will be mapped to "utmtid" parameter
    sku -- Product Code. This is the sku code for a given product, will be mapped to "utmipc" parameter
    name -- Product Name, will be mapped to "utmipn" parameter
    variation -- Variations on an item, will be mapped to "utmiva" parameter
    price -- Unit Price. Value is set to numbers only, will be mapped to "utmipr" parameter
    quantity -- Unit Quantity, will be mapped to "utmiqt" parameter

    '''

    def __init__(self):
        self.order_id = None
        self.sku = None
        self.name = None
        self.variation = None
        self.price = None
        self.quantity = 1

    def validate(self):
        if not self.sku:
            raise exceptions.ValidationError('sku/product is a required parameter')


class Page(object):
    '''
    Contains all parameters needed for tracking a page

    Properties:
    path -- Page request URI, will be mapped to "utmp" parameter
    title -- Page title, will be mapped to "utmdt" parameter
    charset -- Charset encoding, will be mapped to "utmcs" parameter
    referrer -- Referer URL, will be mapped to "utmr" parameter
    load_time -- Page load time in milliseconds, will be encoded into "utme" parameter.

    '''
    REFERRER_INTERNAL = '0'

    def __init__(self, path):
        self.path = None
        self.title = None
        self.charset = None
        self.referrer = None
        self.load_time = None

        if path:
            self.path = path

    def __setattr__(self, name, value):
        if name == 'path':
            if value and value != '':
                if value[0] != '/':
                    raise ValueError('The page path should always start with a slash ("/").')
        elif name == 'load_time':
            if value and not isinstance(value, int):
                raise ValueError('Page load time must be specified in integer milliseconds.')

        object.__setattr__(self, name, value)


class Session(object):
    '''
    You should serialize this object and store it in the user session to keep it
    persistent between requests (similar to the "__umtb" cookie of the GA Javascript client).

    Properties:
    session_id -- A unique per-session ID, will be mapped to "utmhid" parameter
    track_count -- The amount of pageviews that were tracked within this session so far,
                   will be part of the "__utmb" cookie parameter.
                   Will get incremented automatically upon each request
    start_time -- Timestamp of the start of this new session, will be part of the "__utmb" cookie parameter

    '''
    def __init__(self):
        self.session_id = utils.get_32bit_random_num()
        self.track_count = 0
        self.start_time = datetime.utcnow()

    @staticmethod
    def generate_session_id():
        return utils.get_32bit_random_num()

    def extract_from_utmb(self, utmb):
        '''
        Will extract information for the "trackCount" and "startTime"
        properties from the given "__utmb" cookie value.
        '''
        parts = utmb.split('.')
        if len(parts) != 4:
            raise ValueError('The given "__utmb" cookie value is invalid.')

        self.track_count = int(parts[1])
        self.start_time = utils.convert_ga_timestamp(parts[3])

        return self


class SocialInteraction(object):
    '''

    Properties:
    action -- Required. A string representing the social action being tracked,
              will be mapped to "utmsa" parameter
    network -- Required. A string representing the social network being tracked,
               will be mapped to "utmsn" parameter
    target -- Optional. A string representing the URL (or resource) which receives the action.

    '''

    def __init__(self, action=None, network=None, target=None):
        self.action = action
        self.network = network
        self.target = target

    def validate(self):
        if not(self.action and self.network):
            raise exceptions.ValidationError('Social interactions need to have at least the "network" and "action" attributes defined.')


class Transaction(object):
    '''
    Represents parameters for a Transaction call

    Properties:
    order_id -- Order ID, will be mapped to "utmtid" parameter
    affiliation -- Affiliation, Will be mapped to "utmtst" parameter
    total -- Total Cost, will be mapped to "utmtto" parameter
    tax -- Tax Cost, will be mapped to "utmttx" parameter
    shipping -- Shipping Cost, values as for unit and price, will be mapped to "utmtsp" parameter
    city -- Billing City, will be mapped to "utmtci" parameter
    state -- Billing Region, will be mapped to "utmtrg" parameter
    country -- Billing Country, will be mapped to "utmtco" parameter
    items -- @entity.Items in a transaction

    '''
    def __init__(self):
        self.items = []
        self.order_id = None
        self.affiliation = None
        self.total = None
        self.tax = None
        self.shipping = None
        self.city = None
        self.state = None
        self.country = None

    def __setattr__(self, name, value):
        if name == 'order_id':
            for itm in self.items:
                itm.order_id = value
        object.__setattr__(self, name, value)

    def validate(self):
        if len(self.items) == 0:
            raise exceptions.ValidationError('Transaction need to consist of at least one item')

    def add_item(self, item):
        ''' item of type entities.Item '''
        if isinstance(item, Item):
            item.order_id = self.order_id
            self.items.append(item)


class Visitor(object):
    '''
    You should serialize this object and store it in the user database to keep it
    persistent for the same user permanently (similar to the "__umta" cookie of
    the GA Javascript client).

    Properties:
    unique_id -- Unique user ID, will be part of the "__utma" cookie parameter
    first_visit_time -- Time of the very first visit of this user, will be part of the "__utma" cookie parameter
    previous_visit_time -- Time of the previous visit of this user, will be part of the "__utma" cookie parameter
    current_visit_time -- Time of the current visit of this user, will be part of the "__utma" cookie parameter
    visit_count -- Amount of total visits by this user, will be part of the "__utma" cookie parameter
    ip_address -- IP Address of the end user, will be mapped to "utmip" parameter and "X-Forwarded-For" request header
    user_agent -- User agent string of the end user, will be mapped to "User-Agent" request header
    locale -- Locale string (country part optional) will be mapped to "utmul" parameter
    flash_version -- Visitor's Flash version, will be maped to "utmfl" parameter
    java_enabled -- Visitor's Java support, will be mapped to "utmje" parameter
    screen_colour_depth -- Visitor's screen color depth, will be mapped to "utmsc" parameter
    screen_resolution -- Visitor's screen resolution, will be mapped to "utmsr" parameter
    '''
    def __init__(self):
        now = datetime.utcnow()

        self.unique_id = None
        self.first_visit_time = now
        self.previous_visit_time = now
        self.current_visit_time = now
        self.visit_count = 1
        self.ip_address = None
        self.user_agent = None
        self.locale = None
        self.flash_version = None
        self.java_enabled = None
        self.screen_colour_depth = None
        self.screen_resolution = None

    def __setattr__(self, name, value):
        if name == 'unique_id':
            if value and (value < 0 or value > 0x7fffffff):
                raise ValueError('Visitor unique ID has to be a 32-bit integer between 0 and 0x7fffffff')
        object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        if name == 'unique_id':
            tmp = object.__getattribute__(self, name)
            if tmp is None:
                self.unique_id = self.generate_unique_id()
        return object.__getattribute__(self, name)

    def __getstate__(self):
        state = self.__dict__
        if state.get('user_agent') is None:
            state['unique_id'] = self.generate_unique_id()

        return state

    def extract_from_utma(self, utma):
        '''
        Will extract information for the "unique_id", "first_visit_time", "previous_visit_time",
        "current_visit_time" and "visit_count" properties from the given "__utma" cookie value.
        '''
        parts = utma.split('.')
        if len(parts) != 6:
            raise ValueError('The given "__utma" cookie value is invalid.')

        self.unique_id = int(parts[1])
        self.first_visit_time = utils.convert_ga_timestamp(parts[2])
        self.previous_visit_time = utils.convert_ga_timestamp(parts[3])
        self.current_visit_time = utils.convert_ga_timestamp(parts[4])
        self.visit_count = int(parts[5])

        return self

    def extract_from_server_meta(self, meta):
        '''
        Will extract information for the "ip_address", "user_agent" and "locale"
        properties from the given WSGI REQUEST META variable or equivalent.
        '''
        if 'REMOTE_ADDR' in meta and meta['REMOTE_ADDR']:
            ip = None
            for key in ('HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR'):
                if key in meta and not ip:
                    ips = meta.get(key, '').split(',')
                    ip = ips[-1].strip()
                    if not utils.is_valid_ip(ip):
                        ip = ''
                    if utils.is_private_ip(ip):
                        ip = ''
            if ip:
                self.ip_address = ip

        if 'HTTP_USER_AGENT' in meta and meta['HTTP_USER_AGENT']:
            self.user_agent = meta['HTTP_USER_AGENT']

        if 'HTTP_ACCEPT_LANGUAGE' in meta and meta['HTTP_ACCEPT_LANGUAGE']:
            user_locals = []
            matched_locales = utils.validate_locale(meta['HTTP_ACCEPT_LANGUAGE'])
            if matched_locales:
                lang_lst = map((lambda x: x.replace('-', '_')), (i[1] for i in matched_locales))
                quality_lst = map((lambda x: x and x or 1), (float(i[4] and i[4] or '0') for i in matched_locales))
                lang_quality_map = map((lambda x, y: (x, y)), lang_lst, quality_lst)
                user_locals = [x[0] for x in sorted(lang_quality_map, key=itemgetter(1), reverse=True)]

            if user_locals:
                self.locale = user_locals[0]

        return self

    def generate_hash(self):
        '''Generates a hashed value from user-specific properties.'''
        tmpstr = "%s%s%s" % (self.user_agent, self.screen_resolution, self.screen_colour_depth)
        return utils.generate_hash(tmpstr)

    def generate_unique_id(self):
        '''Generates a unique user ID from the current user-specific properties.'''
        return ((utils.get_32bit_random_num() ^ self.generate_hash()) & 0x7fffffff)

    def add_session(self, session):
        '''
        Updates the "previousVisitTime", "currentVisitTime" and "visitCount"
        fields based on the given session object.
        '''
        start_time = session.start_time
        if start_time != self.current_visit_time:
            self.previous_visit_time = self.current_visit_time
            self.current_visit_time = start_time
            self.visit_count = self.visit_count + 1
