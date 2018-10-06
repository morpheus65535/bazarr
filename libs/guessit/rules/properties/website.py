#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Website property.
"""
from pkg_resources import resource_stream  # @UnresolvedImport
from rebulk.remodule import re

from rebulk import Rebulk, Rule, RemoveMatch
from ..common import seps
from ..common.formatters import cleanup
from ..common.validators import seps_surround
from ...reutils import build_or_pattern


def website():
    """
    Builder for rebulk object.
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE).string_defaults(ignore_case=True)
    rebulk.defaults(name="website")

    tlds = [l.strip().decode('utf-8')
            for l in resource_stream('guessit', 'tlds-alpha-by-domain.txt').readlines()
            if b'--' not in l][1:]  # All registered domain extension

    safe_tlds = ['com', 'org', 'net']  # For sure a website extension
    safe_subdomains = ['www']  # For sure a website subdomain
    safe_prefix = ['co', 'com', 'org', 'net']  # Those words before a tlds are sure

    website_prefixes = ['from']

    rebulk.regex(r'(?:[^a-z0-9]|^)((?:'+build_or_pattern(safe_subdomains) +
                 r'\.)+(?:[a-z-]+\.)+(?:'+build_or_pattern(tlds) +
                 r'))(?:[^a-z0-9]|$)',
                 children=True)
    rebulk.regex(r'(?:[^a-z0-9]|^)((?:'+build_or_pattern(safe_subdomains) +
                 r'\.)*[a-z-]+\.(?:'+build_or_pattern(safe_tlds) +
                 r'))(?:[^a-z0-9]|$)',
                 safe_subdomains=safe_subdomains, safe_tlds=safe_tlds, children=True)
    rebulk.regex(r'(?:[^a-z0-9]|^)((?:'+build_or_pattern(safe_subdomains) +
                 r'\.)*[a-z-]+\.(?:'+build_or_pattern(safe_prefix) +
                 r'\.)+(?:'+build_or_pattern(tlds) +
                 r'))(?:[^a-z0-9]|$)',
                 safe_subdomains=safe_subdomains, safe_prefix=safe_prefix, tlds=tlds, children=True)

    rebulk.string(*website_prefixes,
                  validator=seps_surround, private=True, tags=['website.prefix'])

    class PreferTitleOverWebsite(Rule):
        """
        If found match is more likely a title, remove website.
        """
        consequence = RemoveMatch

        @staticmethod
        def valid_followers(match):
            """
            Validator for next website matches
            """
            return any(name in ['season', 'episode', 'year'] for name in match.names)

        def when(self, matches, context):
            to_remove = []
            for website_match in matches.named('website'):
                safe = False
                for safe_start in safe_subdomains + safe_prefix:
                    if website_match.value.lower().startswith(safe_start):
                        safe = True
                        break
                if not safe:
                    suffix = matches.next(website_match, PreferTitleOverWebsite.valid_followers, 0)
                    if suffix:
                        to_remove.append(website_match)
            return to_remove

    rebulk.rules(PreferTitleOverWebsite, ValidateWebsitePrefix)

    return rebulk


class ValidateWebsitePrefix(Rule):
    """
    Validate website prefixes
    """
    priority = 64
    consequence = RemoveMatch

    def when(self, matches, context):
        to_remove = []
        for prefix in matches.tagged('website.prefix'):
            website_match = matches.next(prefix, predicate=lambda match: match.name == 'website', index=0)
            if (not website_match or
                    matches.holes(prefix.end, website_match.start,
                                  formatter=cleanup, seps=seps, predicate=lambda match: match.value)):
                to_remove.append(prefix)
        return to_remove
