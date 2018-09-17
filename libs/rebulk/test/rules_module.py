#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, invalid-name, len-as-condition
from ..match import Match
from ..rules import Rule


class Rule3(Rule):
    def when(self, matches, context):
        return context.get('when')

    def then(self, matches, when_response, context):
        assert when_response in [True, False]
        matches.append(Match(3, 4))


class Rule2(Rule):
    dependency = Rule3

    def when(self, matches, context):
        return True

    def then(self, matches, when_response, context):
        assert when_response
        matches.append(Match(3, 4))


class Rule1(Rule):
    dependency = Rule2

    def when(self, matches, context):
        return True

    def then(self, matches, when_response, context):
        assert when_response
        matches.clear()


class Rule0(Rule):
    dependency = Rule1

    def when(self, matches, context):
        return True

    def then(self, matches, when_response, context):
        assert when_response
        matches.append(Match(3, 4))


class Rule1Disabled(Rule1):
    name = "Disabled Rule1"

    def enabled(self, context):
        return False
