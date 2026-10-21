#!/usr/bin/env python
"""
Define simple search patterns in bulk to perform advanced matching on any string.
"""

from .key import Key
from .processors import POST_PROCESS, PRE_PROCESS, ConflictSolver, PrivateRemover
from .rebulk import Rebulk
from .remodule import REGEX_ENABLED
from .rules import AppendMatch, AppendTags, CustomRule, RemoveMatch, RemoveTags, RenameMatch, Rule

__all__ = [
    "POST_PROCESS",
    "PRE_PROCESS",
    "REGEX_ENABLED",
    "AppendMatch",
    "AppendTags",
    "ConflictSolver",
    "CustomRule",
    "Key",
    "PrivateRemover",
    "Rebulk",
    "RemoveMatch",
    "RemoveTags",
    "RenameMatch",
    "Rule",
]
