#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define simple search patterns in bulk to perform advanced matching on any string.
"""
#  pylint:disable=import-self
from .rebulk import Rebulk
from .rules import Rule, CustomRule, AppendMatch, RemoveMatch, RenameMatch, AppendTags, RemoveTags
from .processors import ConflictSolver, PrivateRemover, POST_PROCESS, PRE_PROCESS
from .pattern import REGEX_AVAILABLE
