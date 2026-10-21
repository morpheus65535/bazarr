#!/usr/bin/env python
"""Shared pytest configuration for the guessit test suite."""

import rebulk.debug

# Run the whole corpus with rebulk's declared-key check on (Toilal/rebulk#72):
# every match named after a declared Key (guessit.rules.common.keys, wired via
# declare_keys) must hold a value of the key's value_type. This turns the ~2300
# YAML cases into a contract test for the registry's types — a formatter that
# stops producing the declared type fails fast here instead of silently.
rebulk.debug.CHECK_DECLARED_KEYS = True
