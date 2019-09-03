# -*- coding: utf-8 -*-

import logging
import calendar
from math import floor
from pyga.entities import Campaign, CustomVariable, Event, Item, Page, Session, SocialInteraction, Transaction, Visitor
import pyga.utils as utils
try:
    from urllib import urlencode
    from urllib2 import Request as urllib_request
    from urllib2 import urlopen
except ImportError as e:
    from urllib.parse import urlencode
    from urllib.request import Request as urllib_request
    from urllib.request import urlopen

__author__ = "Arun KR (kra3) <the1.arun@gmail.com"
__license__ = "Simplified BSD"
__version__ = '2.6.1'

logger = logging.getLogger(__name__)


class Q(object):
    REQ_ARRAY = []

    def add_wrapped_request(self, req_wrapper):
        self.REQ_ARRAY.append(req_wrapper)


class GIFRequest(object):
    '''

    Properties:
    type -- Indicates the type of request, will be mapped to "utmt" parameter
    config -- base.Config object
    x_forwarded_for --
    user_agent -- User Agent String

    '''
    def __init__(self, config):
        self.type = None
        self.config = None
        self.x_forwarded_for = None
        self.user_agent = None
        self.__Q = Q()
        if isinstance(config, Config):
            self.config = config

    def build_http_request(self):
        params = self.build_parameters()
        query_string = urlencode(params.get_parameters())
        query_string = query_string.replace('+', '%20')

        # Mimic Javascript's encodeURIComponent() encoding for the query
        # string just to be sure we are 100% consistent with GA's Javascript client
        query_string = utils.convert_to_uri_component_encoding(query_string)

        # Recent versions of ga.js use HTTP POST requests if the query string is too long
        use_post = len(query_string) > 2036

        if not use_post:
            url = '%s?%s' % (self.config.endpoint, query_string)
            post = None
        else:
            url = self.config.endpoint
            post = query_string

        headers = {}
        headers['Host'] = self.config.endpoint.split('/')[2]
        headers['User-Agent'] = self.user_agent or ''
        headers['X-Forwarded-For'] = self.x_forwarded_for and self.x_forwarded_for or ''

        if use_post:
            # Don't ask me why "text/plain", but ga.js says so :)
            headers['Content-Type'] = 'text/plain'
            headers['Content-Length'] = len(query_string)

        logger.debug(url)
        if post:
            logger.debug(post)
        return urllib_request(url, post, headers)

    def build_parameters(self):
        '''Marker implementation'''
        return Parameters()

    def __send(self):
        request = self.build_http_request()
        response = None

        #  Do not actually send the request if endpoint host is set to null
        if self.config.endpoint:
            response = urlopen(
                request, timeout=self.config.request_timeout)

        return response

    def fire(self):
        '''
        Simply delegates to send() if config option "queue_requests" is disabled
        else enqueues the request into Q object: you should call pyga.shutdowon
        as last statement, to actually send out all queued requests.
        '''
        if self.config.queue_requests:
            # Queuing results. You should call pyga.shutdown as last statement to send out requests.
            self.__Q.add_wrapped_request((lambda: self.__send()))
        else:
            self.__send()


class Request(GIFRequest):
    TYPE_PAGE = None
    TYPE_EVENT = 'event'
    TYPE_TRANSACTION = 'tran'
    TYPE_ITEM = 'item'
    TYPE_SOCIAL = 'social'

    '''
    This type of request is deprecated in favor of encoding custom variables
    within the "utme" parameter, but we include it here for completeness
    '''
    TYPE_CUSTOMVARIABLE = 'var'

    X10_CUSTOMVAR_NAME_PROJECT_ID = 8
    X10_CUSTOMVAR_VALUE_PROJCT_ID = 9
    X10_CUSTOMVAR_SCOPE_PROJECT_ID = 11

    def __init__(self, config, tracker, visitor, session):
        super(Request, self).__init__(config)
        self.tracker = tracker
        self.visitor = visitor
        self.session = session

    def build_http_request(self):
        self.x_forwarded_for = self.visitor.ip_address
        self.user_agent = self.visitor.user_agent

        # Increment session track counter for each request
        self.session.track_count = self.session.track_count + 1

        #http://code.google.com/intl/de-DE/apis/analytics/docs/tracking/eventTrackerGuide.html#implementationConsiderations
        if self.session.track_count > 500:
            logger.warning('Google Analytics does not guarantee to process more than 500 requests per session.')

        if self.tracker.campaign:
            self.tracker.campaign.response_count = self.tracker.campaign.response_count + 1

        return super(Request, self).build_http_request()

    def build_parameters(self):
        params = Parameters()
        params.utmac = self.tracker.account_id
        params.utmhn = self.tracker.domain_name
        params.utmt = self.get_type()
        params.utmn = utils.get_32bit_random_num()
        '''
        The "utmip" parameter is only relevant if a mobile analytics ID
        (MO-XXXXXX-X) was given
        '''
        params.utmip = self.visitor.ip_address
        params.aip = self.tracker.config.anonimize_ip_address and 1 or None

        # Add override User-Agent parameter (&ua) and override IP address
        # parameter (&uip). Note that the override IP address parameter is
        # always anonymized, as if &aip were present (see
        # https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters#uip)
        params.ua = self.visitor.user_agent
        params.uip = utils.anonymize_ip(self.visitor.ip_address)

        if params.aip:
            # If anonimization of ip enabled? then!
            params.utmip = utils.anonymize_ip(params.utmip)

        params.utmhid = self.session.session_id
        params.utms = self.session.track_count
        params = self.build_visitor_parameters(params)
        params = self.build_custom_variable_parameters(params)
        params = self.build_campaign_parameters(params)
        params = self.build_cookie_parameters(params)
        return params

    def build_visitor_parameters(self, params):
        if self.visitor.locale:
            params.utmul = self.visitor.locale.replace('_', '-').lower()

        if self.visitor.flash_version:
            params.utmfl = self.visitor.flash_version

        if self.visitor.java_enabled:
            params.utje = self.visitor.java_enabled

        if self.visitor.screen_colour_depth:
            params.utmsc = '%s-bit' % (self.visitor.screen_colour_depth)

        if self.visitor.screen_resolution:
            params.utmsr = self.visitor.screen_resolution

        return params

    def build_custom_variable_parameters(self, params):
        custom_vars = self.tracker.custom_variables

        if custom_vars:
            if len(custom_vars) > 5:
                logger.warning('The sum of all custom variables cannot exceed 5 in any given request.')

            x10 = X10()
            x10.clear_key(self.X10_CUSTOMVAR_NAME_PROJECT_ID)
            x10.clear_key(self.X10_CUSTOMVAR_VALUE_PROJCT_ID)
            x10.clear_key(self.X10_CUSTOMVAR_SCOPE_PROJECT_ID)

            for cvar in custom_vars.itervalues():
                name = utils.encode_uri_components(cvar.name)
                value = utils.encode_uri_components(cvar.value)
                x10.set_key(
                    self.X10_CUSTOMVAR_NAME_PROJECT_ID, cvar.index, name)
                x10.set_key(
                    self.X10_CUSTOMVAR_VALUE_PROJCT_ID, cvar.index, value)

                if cvar.scope and cvar.scope != CustomVariable.SCOPE_PAGE:
                    x10.set_key(self.X10_CUSTOMVAR_SCOPE_PROJECT_ID,
                                cvar.index, cvar.scope)

            params.utme = '%s%s' % (params.utme, x10.render_url_string())

        return params

    def build_campaign_parameters(self, params):
        campaign = self.tracker.campaign
        if campaign:
            params._utmz = '%s.%s.%s.%s.' % (
                self._generate_domain_hash(),
                calendar.timegm(campaign.creation_time.timetuple()),
                self.visitor.visit_count,
                campaign.response_count,
            )

            param_map = {
                'utmcid': campaign.id,
                'utmcsr': campaign.source,
                'utmgclid': campaign.g_click_id,
                'utmdclid': campaign.d_click_id,
                'utmccn': campaign.name,
                'utmcmd': campaign.medium,
                'utmctr': campaign.term,
                'utmcct': campaign.content,
            }

            for k, v in param_map.items():
                if v:
                    # Only spaces and pluses get escaped in gaforflash and ga.js, so we do the same
                    params._utmz = '%s%s=%s%s' % (params._utmz, k,
                                                  v.replace('+', '%20').replace(' ', '%20'),
                                                  Campaign.CAMPAIGN_DELIMITER
                                                  )

            params._utmz = params._utmz.rstrip(Campaign.CAMPAIGN_DELIMITER)

        return params

    def build_cookie_parameters(self, params):
        domain_hash = self._generate_domain_hash()
        params._utma = "%s.%s.%s.%s.%s.%s" % (
            domain_hash,
            self.visitor.unique_id,
            calendar.timegm(self.visitor.first_visit_time.timetuple()),
            calendar.timegm(self.visitor.previous_visit_time.timetuple()),
            calendar.timegm(self.visitor.current_visit_time.timetuple()),
            self.visitor.visit_count
        )
        params._utmb = '%s.%s.10.%s' % (
            domain_hash,
            self.session.track_count,
            calendar.timegm(self.session.start_time.timetuple()),
        )
        params._utmc = domain_hash
        cookies = []
        cookies.append('__utma=%s;' % params._utma)
        if params._utmz:
            cookies.append('__utmz=%s;' % params._utmz)
        if params._utmv:
            cookies.append('__utmv=%s;' % params._utmv)

        params.utmcc = '+'.join(cookies)
        return params

    def _generate_domain_hash(self):
        hash_val = 1
        if self.tracker.allow_hash:
            hash_val = utils.generate_hash(self.tracker.domain_name)

        return hash_val


class ItemRequest(Request):
    def __init__(self, config, tracker, visitor, session, item):
        super(ItemRequest, self).__init__(config, tracker, visitor, session)
        self.item = item

    def get_type(self):
        return ItemRequest.TYPE_ITEM

    def build_parameters(self):
        params = super(ItemRequest, self).build_parameters()
        params.utmtid = self.item.order_id
        params.utmipc = self.item.sku
        params.utmipn = self.item.name
        params.utmiva = self.item.variation
        params.utmipr = self.item.price
        params.utmiqt = self.item.quantity
        return params

    def build_visitor_parameters(self, parameters):
        '''
        The GA Javascript client doesn't send any visitor information for
        e-commerce requests, so we don't either.
        '''
        return parameters

    def build_custom_variable_parameters(self, parameters):
        '''
        The GA Javascript client doesn't send any custom variables for
        e-commerce requests, so we don't either.
        '''
        return parameters


class PageViewRequest(Request):
    X10_SITESPEED_PROJECT_ID = 14

    def __init__(self, config, tracker, visitor, session, page):
        super(
            PageViewRequest, self).__init__(config, tracker, visitor, session)
        self.page = page

    def get_type(self):
        return PageViewRequest.TYPE_PAGE

    def build_parameters(self):
        params = super(PageViewRequest, self).build_parameters()
        params.utmp = self.page.path
        params.utmdt = self.page.title

        if self.page.charset:
            params.utmcs = self.page.charset

        if self.page.referrer:
            params.utmr = self.page.referrer

        if self.page.load_time:
            if params.utmn % 100 < self.config.site_speed_sample_rate:
                x10 = X10()
                x10.clear_key(self.X10_SITESPEED_PROJECT_ID)
                x10.clear_value(self.X10_SITESPEED_PROJECT_ID)

                # from ga.js
                key = max(min(floor(self.page.load_time / 100), 5000), 0) * 100
                x10.set_key(
                    self.X10_SITESPEED_PROJECT_ID, X10.OBJECT_KEY_NUM, key)
                x10.set_value(self.X10_SITESPEED_PROJECT_ID,
                              X10.VALUE_VALUE_NUM, self.page.load_time)
                params.utme = '%s%s' % (params.utme, x10.render_url_string())

        return params


class EventRequest(Request):
    X10_EVENT_PROJECT_ID = 5

    def __init__(self, config, tracker, visitor, session, event):
        super(EventRequest, self).__init__(config, tracker, visitor, session)
        self.event = event

    def get_type(self):
        return EventRequest.TYPE_EVENT

    def build_parameters(self):
        params = super(EventRequest, self).build_parameters()
        x10 = X10()
        x10.clear_key(self.X10_EVENT_PROJECT_ID)
        x10.clear_value(self.X10_EVENT_PROJECT_ID)
        x10.set_key(self.X10_EVENT_PROJECT_ID, X10.OBJECT_KEY_NUM,
                    self.event.category)
        x10.set_key(
            self.X10_EVENT_PROJECT_ID, X10.TYPE_KEY_NUM, self.event.action)

        if self.event.label:
            x10.set_key(self.X10_EVENT_PROJECT_ID,
                        X10.LABEL_KEY_NUM, self.event.label)

        if self.event.value:
            x10.set_value(self.X10_EVENT_PROJECT_ID,
                          X10.VALUE_VALUE_NUM, self.event.value)

        params.utme = "%s%s" % (params.utme, x10.render_url_string())

        if self.event.noninteraction:
            params.utmni = 1

        return params


class SocialInteractionRequest(Request):
    def __init__(self, config, tracker, visitor, session, social_interaction, page):
        super(SocialInteractionRequest, self).__init__(config,
                                                       tracker, visitor, session)
        self.social_interaction = social_interaction
        self.page = page

    def get_type(self):
        return SocialInteractionRequest.TYPE_SOCIAL

    def build_parameters(self):
        params = super(SocialInteractionRequest, self).build_parameters()

        tmppagepath = self.social_interaction.target
        if tmppagepath is None:
            tmppagepath = self.page.path

        params.utmsn = self.social_interaction.network
        params.utmsa = self.social_interaction.action
        params.utmsid = tmppagepath
        return params


class TransactionRequest(Request):
    def __init__(self, config, tracker, visitor, session, transaction):
        super(TransactionRequest, self).__init__(config, tracker,
                                                 visitor, session)
        self.transaction = transaction

    def get_type(self):
        return TransactionRequest.TYPE_TRANSACTION

    def build_parameters(self):
        params = super(TransactionRequest, self).build_parameters()
        params.utmtid = self.transaction.order_id
        params.utmtst = self.transaction.affiliation
        params.utmtto = self.transaction.total
        params.utmttx = self.transaction.tax
        params.utmtsp = self.transaction.shipping
        params.utmtci = self.transaction.city
        params.utmtrg = self.transaction.state
        params.utmtco = self.transaction.country
        return params

    def build_visitor_parameters(self, parameters):
        '''
        The GA Javascript client doesn't send any visitor information for
        e-commerce requests, so we don't either.
        '''
        return parameters

    def build_custom_variable_parameters(self, parameters):
        '''
        The GA Javascript client doesn't send any custom variables for
        e-commerce requests, so we don't either.
        '''
        return parameters


class Config(object):
    '''
    Configurations for Google Analytics: Server Side

    Properties:
    error_severity -- How strict should errors get handled? After all,
        we do just do some tracking stuff here, and errors shouldn't
        break an application's functionality in production.
        RECOMMENDATION: Exceptions during deveopment, warnings in production.
    queue_requests --  Whether to just queue all requests on HttpRequest.fire()
        and actually send them on shutdown after all other tasks are done.
        This has two advantages:
        1) It effectively doesn't affect app performance
        2) It can e.g. handle custom variables that were set after scheduling a request
    fire_and_forget -- Whether to make asynchronous requests to GA without
        waiting for any response (speeds up doing requests).
    logging_callback -- Logging callback, registered via setLoggingCallback().
        Will be fired whenever a request gets sent out and receives the
        full HTTP request as the first and the full HTTP response
        (or null if the "fireAndForget" option or simulation mode are used) as the 2nd argument.
    request_timeout -- Seconds (float allowed) to wait until timeout when
        connecting to the Google analytics endpoint host.
    endpoint -- Google Analytics tracking request endpoint. Can be set to null to
        silently simulate (and log) requests without actually sending them.
    anonimize_ip_address -- Whether to anonymize IP addresses within Google Analytics
        by stripping the last IP address block, will be mapped to "aip" parameter.
    site_speed_sample_rate -- Defines a new sample set size (0-100) for
        Site Speed data collection. By default, a fixed 1% sampling of your site
        visitors make up the data pool from which the Site Speed metrics are derived.

    '''
    ERROR_SEVERITY_SILECE = 0
    ERROR_SEVERITY_PRINT = 1
    ERROR_SEVERITY_RAISE = 2

    def __init__(self):
        self.error_severity = Config.ERROR_SEVERITY_RAISE
        self.queue_requests = False
        # self.fire_and_forget = False      # not supported as of now
        # self.logging_callback = False     # not supported as of now
        self.request_timeout = 1
        self.endpoint = 'http://www.google-analytics.com/__utm.gif'
        self.anonimize_ip_address = False
        self.site_speed_sample_rate = 1

    def __setattr__(self, name, value):
        if name == 'site_speed_sample_rate':
            if value and (value < 0 or value > 100):
                raise ValueError('For consistency with ga.js, sample rates must be specified as a number between 0 and 100.')
        object.__setattr__(self, name, value)


class Parameters(object):
    '''
    This simple class is mainly meant to be a well-documented overview
    of all possible GA tracking parameters.

    http://code.google.com/apis/analytics/docs/tracking/gaTrackingTroubleshooting.html#gifParameters

    General Parameters:
    utmwv -- Google Analytics client version
    utmac -- Google Analytics account ID
    utmhn -- Host Name
    utmt -- Indicates the type of request, which is one of null (for page),
            "event", "tran", "item", "social", "var" (deprecated) or "error"
            (used by ga.js for internal client error logging).
    utms -- Contains the amount of requests done in this session. Added in ga.js v4.9.2.
    utmn -- Unique ID (random number) generated for each GIF request
    utmcc -- Contains all cookie values, see below
    utme -- Extensible Parameter, used for events and custom variables
    utmni -- Event "non-interaction" parameter. By default, the event hit will impact a visitor's bounce rate.
             By setting this parameter to 1, this event hit will not be used in bounce rate calculations.
    aip -- Whether to anonymize IP addresses within Google Analytics by stripping the last IP address block, either null or 1
    utmu --  Used for GA-internal statistical client function usage and error tracking,
             not implemented in php-ga as of now, but here for documentation completeness.
             http://glucik.blogspot.com/2011/02/utmu-google-analytics-request-parameter.html

    Page Parameters:
    utmp -- Page request URI
    utmdt -- Page title
    utmcs -- Charset encoding (default "-")
    utmr -- Referer URL (default "-" or "0" for internal purposes)

    Visitor Parameters:
    utmip -- IP Address of the end user, found in GA for Mobile examples, but sadly seems to be ignored in normal GA use
    utmul -- Visitor's locale string (all lower-case, country part optional)
    utmfl -- Visitor's Flash version (default "-")
    utmje -- Visitor's Java support, either 0 or 1 (default "-")
    utmsc -- Visitor's screen color depth
    utmsr -- Visitor's screen resolution
    _utma -- Visitor tracking cookie parameter.

    Session Parameters:
    utmhid -- Hit id for revenue per page tracking for AdSense, a random per-session ID
    _utmb -- Session timeout cookie parameter.
    _utmc -- Session tracking cookie parameter.
    utmipc -- Product Code. This is the sku code for a given product.
    utmipn -- Product Name
    utmipr -- Unit Price. Value is set to numbers only.
    utmiqt -- Unit Quantity.
    utmiva -- Variations on an item.
    utmtid -- Order ID.
    utmtst -- Affiliation
    utmtto -- Total Cost
    utmttx -- Tax Cost
    utmtsp -- Shipping Cost
    utmtci -- Billing City
    utmtrg -- Billing Region
    utmtco -- Billing Country

    Campaign Parameters:
    utmcn -- Starts a new campaign session. Either utmcn or utmcr is present on any given request,
             but never both at the same time. Changes the campaign tracking data;
             but does not start a new session. Either 1 or not set.
             Found in gaforflash but not in ga.js, so we do not use it,
             but it will stay here for documentation completeness.
    utmcr -- Indicates a repeat campaign visit. This is set when any subsequent clicks occur on the
             same link. Either utmcn or utmcr is present on any given request,
             but never both at the same time. Either 1 or not set.
             Found in gaforflash but not in ga.js, so we do not use it,
             but it will stay here for documentation completeness.
    utmcid -- Campaign ID, a.k.a. "utm_id" query parameter for ga.js
    utmcsr -- Source, a.k.a. "utm_source" query parameter for ga.js
    utmgclid -- Google AdWords Click ID, a.k.a. "gclid" query parameter for ga.js
    utmdclid -- Not known for sure, but expected to be a DoubleClick Ad Click ID.
    utmccn -- Name, a.k.a. "utm_campaign" query parameter for ga.js
    utmcmd -- Medium, a.k.a. "utm_medium" query parameter for ga.js
    utmctr -- Terms/Keywords, a.k.a. "utm_term" query parameter for ga.js
    utmcct -- Ad Content Description, a.k.a. "utm_content" query parameter for ga.js
    utmcvr -- Unknown so far. Found in ga.js.
    _utmz -- Campaign tracking cookie parameter.

    Social Tracking Parameters:
    utmsn -- The network on which the action occurs
    utmsa -- The type of action that happens
    utmsid -- The page URL from which the action occurred.

    Google Website Optimizer (GWO) parameters:
    _utmx -- Website Optimizer cookie parameter.

    Custom Variables parameters (deprecated):
    _utmv -- Deprecated custom variables cookie parameter.

    '''

    def __init__(self):
        # General Parameters
        self.utmwv = Tracker.VERSION
        self.utmac = ''
        self.utmhn = ''
        self.utmt = ''
        self.utms = ''
        self.utmn = ''
        self.utmcc = ''
        self.utme = ''
        self.utmni = ''
        self.aip = ''
        self.utmu = ''

        # Page Parameters
        self.utmp = ''
        self.utmdt = ''
        self.utmcs = '-'
        self.utmr = '-'

        # Visitor Parameters
        self.utmip = ''
        self.utmul = ''
        self.utmfl = '-'
        self.utmje = '-'
        self.utmsc = ''
        self.utmsr = ''
        '''
        Visitor tracking cookie __utma

         This cookie is typically written to the browser upon the first
         visit to your site from that web browser. If the cookie has been
         deleted by the browser operator, and the browser subsequently
         visits your site, a new __utma cookie is written with a different unique ID.

         This cookie is used to determine unique visitors to your site and
         it is updated with each page view. Additionally, this cookie is
         provided with a unique ID that Google Analytics uses to ensure both the
         validity and accessibility of the cookie as an extra security measure.

        Expiration: 2 years from set/update.
        Format: __utma=<domainHash>.<uniqueId>.<firstTime>.<lastTime>.<currentTime>.<sessionCount>
        '''
        self._utma = ''

        # Session Parameters
        self.utmhid = ''
        '''
        Session timeout cookie parameter __utmb

        Will never be sent with requests, but stays here for documentation completeness.

        This cookie is used to establish and continue a user session with your site.
        When a user views a page on your site, the Google Analytics code attempts to update this cookie.
        If it does not find the cookie, a new one is written and a new session is established.

        Each time a user visits a different page on your site, this cookie is updated to expire in 30 minutes,
        thus continuing a single session for as long as user activity continues within 30-minute intervals.

        This cookie expires when a user pauses on a page on your site for longer than 30 minutes.
        You can modify the default length of a user session with the setSessionTimeout() method.

        Expiration: 30 minutes from set/update.

        Format: __utmb=<domainHash>.<trackCount>.<token>.<lastTime>

        '''
        self._utmb = ''
        '''
        Session tracking cookie parameter __utmc

        Will never be sent with requests, but stays here for documentation completeness.

        This cookie operates in conjunction with the __utmb cookie to
        determine whether or not to establish a new session for the user.
        In particular, this cookie is not provided with an expiration date,
        so it expires when the user exits the browser.

        Should a user visit your site, exit the browser and then return to your website within 30 minutes,
        the absence of the __utmc cookie indicates that a new session needs to be established,
        despite the fact that the __utmb cookie has not yet expired.

        Expiration: Not set.

        Format: __utmc=<domainHash>

        '''
        self._utmc = ''
        self.utmipc = ''
        self.utmipn = ''
        self.utmipr = ''
        self.utmiqt = ''
        self.utmiva = ''
        self.utmtid = ''
        self.utmtst = ''
        self.utmtto = ''
        self.utmttx = ''
        self.utmtsp = ''
        self.utmtci = ''
        self.utmtrg = ''
        self.utmtco = ''

        # Campaign Parameters
        self.utmcn = ''
        self.utmcr = ''
        self.utmcid = ''
        self.utmcsr = ''
        self.utmgclid = ''
        self.utmdclid = ''
        self.utmccn = ''
        self.utmcmd = ''
        self.utmctr = ''
        self.utmcct = ''
        self.utmcvr = ''
        '''
        Campaign tracking cookie parameter.

        This cookie stores the type of referral used by the visitor to reach your site,
        whether via a direct method, a referring link, a website search, or a campaign such as an ad or an email link.

        It is used to calculate search engine traffic, ad campaigns and page navigation within your own site.
        The cookie is updated with each page view to your site.

        Expiration: 6 months from set/update.

        Format: __utmz=<domainHash>.<campaignCreation>.<campaignSessions>.<responseCount>.<campaignTracking>

        '''
        self._utmz = ''

        # Social Tracking Parameters
        self.utmsn = ''
        self.utmsa = ''
        self.utmsid = ''

        # Google Website Optimizer (GWO) parameters
        '''
        Website Optimizer cookie parameter.

        This cookie is used by Website Optimizer and only set when Website
        Optimizer is used in combination with GA.
        See the Google Website Optimizer Help Center for details.

        Expiration: 2 years from set/update.
        '''
        self._utmx = ''

        # Custom Variables parameters (deprecated)
        '''
        Deprecated custom variables cookie parameter.

        This cookie parameter is no longer relevant as of migration from setVar() to
        setCustomVar() and hence not supported by this library,
        but will stay here for documentation completeness.

        The __utmv cookie passes the information provided via the setVar() method,
        which you use to create a custom user segment.

        Expiration: 2 years from set/update.

        Format: __utmv=<domainHash>.<value>

        '''
        self._utmv = ''

    def get_parameters(self):
        '''
        Get all gif request parameters out of the class in a dict form.
        Attributes starting with _ are cookie names, so we dont need them.
        '''
        params = {}
        attribs = vars(self)
        for attr in attribs:
            if attr[0] != '_':
                val = getattr(self, attr)
                if val:
                    params[attr] = val

        return params


class Tracker(object):
    '''
    Act like a Manager of all files

    Properties:
    account_id -- Google Analytics account ID, will be mapped to "utmac" parameter
    domain_name -- Host Name, will be mapped to "utmhn" parameter
    allow_hash --  Whether to generate a unique domain hash,
                   default is true to be consistent with the GA Javascript Client
    custom_variables -- CustomVariable instances
    campaign -- Campaign instance
    '''

    '''
    Google Analytics client version on which this library is built upon,
    will be mapped to "utmwv" parameter.

    This doesn't necessarily mean that all features of the corresponding
    ga.js version are implemented but rather that the requests comply
    with these of ga.js.

    http://code.google.com/apis/analytics/docs/gaJS/changelog.html
    '''
    VERSION = '5.3.0'
    config = Config()

    def __init__(self, account_id='', domain_name='', conf=None):
        self.account_id = account_id
        self.domain_name = domain_name
        self.allow_hash = True
        self.custom_variables = {}
        self.campaign = None
        if isinstance(conf, Config):
            Tracker.config = conf

    def __setattr__(self, name, value):
        if name == 'account_id':
            if value and not utils.is_valid_google_account(value):
                raise ValueError(
                    'Given Google Analytics account ID is not valid')

        elif name == 'campaign':
            if isinstance(value, Campaign):
                value.validate()
            else:
                value = None

        object.__setattr__(self, name, value)

    def add_custom_variable(self, custom_var):
        '''
        Equivalent of _setCustomVar() in GA Javascript client
        http://code.google.com/apis/analytics/docs/tracking/gaTrackingCustomVariables.html
        '''
        if not isinstance(custom_var, CustomVariable):
            return

        custom_var.validate()
        index = custom_var.index
        self.custom_variables[index] = custom_var

    def remove_custom_variable(self, index):
        '''Equivalent of _deleteCustomVar() in GA Javascript client.'''
        if index in self.custom_variables:
            del self.custom_variables[index]

    def track_pageview(self, page, session, visitor):
        '''Equivalent of _trackPageview() in GA Javascript client.'''
        params = {
            'config': self.config,
            'tracker': self,
            'visitor': visitor,
            'session': session,
            'page': page,
        }
        request = PageViewRequest(**params)
        request.fire()

    def track_event(self, event, session, visitor):
        '''Equivalent of _trackEvent() in GA Javascript client.'''
        event.validate()

        params = {
            'config': self.config,
            'tracker': self,
            'visitor': visitor,
            'session': session,
            'event': event,
        }
        request = EventRequest(**params)
        request.fire()

    def track_transaction(self, transaction, session, visitor):
        '''Combines _addTrans(), _addItem() (indirectly) and _trackTrans() of GA Javascript client.'''
        transaction.validate()

        params = {
            'config': self.config,
            'tracker': self,
            'visitor': visitor,
            'session': session,
            'transaction': transaction,
        }
        request = TransactionRequest(**params)
        request.fire()

        for item in transaction.items:
            item.validate()

            params = {
                'config': self.config,
                'tracker': self,
                'visitor': visitor,
                'session': session,
                'item': item,
            }
            request = ItemRequest(**params)
            request.fire()

    def track_social(self, social_interaction, page, session, visitor):
        '''Equivalent of _trackSocial() in GA Javascript client.'''
        params = {
            'config': self.config,
            'tracker': self,
            'visitor': visitor,
            'session': session,
            'social_interaction': social_interaction,
            'page': page,
        }
        request = SocialInteractionRequest(**params)
        request.fire()


class X10(object):
    __KEY = 'k'
    __VALUE = 'v'
    __DELIM_BEGIN = '('
    __DELIM_END = ')'
    __DELIM_SET = '*'
    __DELIM_NUM_VALUE = '!'
    __ESCAPE_CHAR_MAP = {
        "'": "'0",
        ')': "'1",
        '*': "'2",
        '!': "'3",
    }
    __MINIMUM = 1

    OBJECT_KEY_NUM = 1
    TYPE_KEY_NUM = 2
    LABEL_KEY_NUM = 3
    VALUE_VALUE_NUM = 1

    def __init__(self):
        self.project_data = {}

    def has_project(self, project_id):
        return project_id in self.project_data

    def set_key(self, project_id, num, value):
        self.__set_internal(project_id, X10.__KEY, num, value)

    def get_key(self, project_id, num):
        return self.__get_internal(project_id, X10.__KEY, num)

    def clear_key(self, project_id):
        self.__clear_internal(project_id, X10.__KEY)

    def set_value(self, project_id, num, value):
        self.__set_internal(project_id, X10.__VALUE, num, value)

    def get_value(self, project_id, num):
        return self.__get_internal(project_id, X10.__VALUE, num)

    def clear_value(self, project_id):
        self.__clear_internal(project_id, X10.__VALUE)

    def __set_internal(self, project_id, _type, num, value):
        '''Shared internal implementation for setting an X10 data type.'''
        if project_id not in self.project_data:
            self.project_data[project_id] = {}

        if _type not in self.project_data[project_id]:
            self.project_data[project_id][_type] = {}

        self.project_data[project_id][_type][num] = value

    def __get_internal(self, project_id, _type, num):
        ''' Shared internal implementation for getting an X10 data type.'''
        if num in self.project_data.get(project_id, {}).get(_type, {}):
            return self.project_data[project_id][_type][num]
        return None

    def __clear_internal(self, project_id, _type):
        '''
        Shared internal implementation for clearing all X10 data
        of a type from a certain project.
        '''
        if project_id in self.project_data and _type in self.project_data[project_id]:
            del self.project_data[project_id][_type]

    def __escape_extensible_value(self, value):
        '''Escape X10 string values to remove ambiguity for special characters.'''
        def _translate(char):
            try:
                return self.__ESCAPE_CHAR_MAP[char]
            except KeyError:
                return char

        return ''.join(map(_translate, str(value)))

    def __render_data_type(self, data):
        '''Given a data array for a certain type, render its string encoding.'''
        result = []
        last_indx = 0

        for indx, entry in sorted(data.items()):
            if entry:
                tmpstr = ''

                # Check if we need to append the number. If the last number was
                # outputted, or if this is the assumed minimum, then we don't.
                if indx != X10.__MINIMUM and indx - 1 != last_indx:
                    tmpstr = '%s%s%s' % (tmpstr, indx, X10.__DELIM_NUM_VALUE)

                tmpstr = '%s%s' % (
                    tmpstr, self.__escape_extensible_value(entry))
                result.append(tmpstr)

            last_indx = indx

        return "%s%s%s" % (X10.__DELIM_BEGIN, X10.__DELIM_SET.join(result), X10.__DELIM_END)

    def __render_project(self, project):
        '''Given a project array, render its string encoding.'''
        result = ''
        need_type_qualifier = False

        for val in X10.__KEY, X10.__VALUE:
            if val in project:
                data = project[val]
                if need_type_qualifier:
                    result = '%s%s' % (result, val)

                result = '%s%s' % (result, self.__render_data_type(data))
                need_type_qualifier = False
            else:
                need_type_qualifier = True

        return result

    def render_url_string(self):
        result = ''
        for project_id, project in self.project_data.items():
            result = '%s%s%s' % (
                result, project_id, self.__render_project(project))

        return result
