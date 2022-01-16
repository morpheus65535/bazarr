"""
Config module.
"""
from importlib import import_module
from typing import Any, List

from rebulk import Rebulk

_regex_prefix = 're:'
_import_prefix = 'import:'
_import_cache = {}
_eval_prefix = 'eval:'
_eval_cache = {}
_pattern_types = ('regex', 'string')
_default_module_names = {
    'validator': 'guessit.rules.common.validators',
    'formatter': 'guessit.rules.common.formatters'
}


def _process_option(name: str, value: Any):
    if name in ('validator', 'conflict_solver', 'formatter'):
        if isinstance(value, dict):
            return {item_key: _process_option(name, item_value) for item_key, item_value in value.items()}
        if value is not None:
            return _process_option_executable(value, _default_module_names.get(name))
    return value


def _import(value: str, default_module_name=None):
    if '.' in value:
        module_name, target = value.rsplit(':', 1)
    else:
        module_name = default_module_name
        target = value
    import_id = module_name + ":" + target
    if import_id in _import_cache:
        return _import_cache[import_id]

    mod = import_module(module_name)

    imported = mod
    for item in target.split("."):
        imported = getattr(imported, item)

    _import_cache[import_id] = imported

    return imported


def _eval(value: str):
    compiled = _eval_cache.get(value)
    if not compiled:
        compiled = compile(value, '<string>', 'eval')
    return eval(compiled)  # pylint:disable=eval-used


def _process_option_executable(value: str, default_module_name=None):
    if value.startswith(_import_prefix):
        value = value[len(_import_prefix):]
        return _import(value, default_module_name)
    if value.startswith(_eval_prefix):
        value = value[len(_eval_prefix):]
        return _eval(value)
    if value.startswith('lambda ') or value.startswith('lambda:'):
        return _eval(value)
    return value


def _process_callable_entry(callable_spec: str, rebulk: Rebulk, entry: dict):
    _process_option_executable(callable_spec)(rebulk, **entry)


def _build_entry_decl(entry, options, value):
    entry_decl = dict(options.get(None, {}))
    if not value.startswith('_'):
        entry_decl['value'] = value
    if isinstance(entry, str):
        if entry.startswith(_regex_prefix):
            entry_decl["regex"] = [entry[len(_regex_prefix):]]
        else:
            entry_decl["string"] = [entry]
    else:
        entry_decl.update(entry)
    if "pattern" in entry_decl:
        legacy_pattern = entry.pop("pattern")
        if legacy_pattern.startswith(_regex_prefix):
            entry_decl["regex"] = [legacy_pattern[len(_regex_prefix):]]
        else:
            entry_decl["string"] = [legacy_pattern]
    return entry_decl


def load_patterns(rebulk: Rebulk,
                  pattern_type: str,
                  patterns: List[str],
                  options: dict = None):
    """
    Load patterns for a prepared config entry
    :param rebulk: Rebulk builder to use.
    :param pattern_type: Pattern type.
    :param patterns: Patterns
    :param options: kwargs options to pass to rebulk pattern function.
    :return:
    """
    default_options = options.get(None) if options else None
    item_options = dict(default_options) if default_options else {}
    pattern_type_option = options.get(pattern_type)
    if pattern_type_option:
        item_options.update(pattern_type_option)
    item_options = {name: _process_option(name, value) for name, value in item_options.items()}
    getattr(rebulk, pattern_type)(*patterns, **item_options)


def load_config_patterns(rebulk: Rebulk,
                         config: dict,
                         options: dict = None):
    """
    Load patterns defined in given config.
    :param rebulk: Rebulk builder to use.
    :param config: dict containing pattern definition.
    :param options: Additional pattern options to use.
    :type options: Dict[Dict[str, str]] A dict where key is the pattern type (regex, string, functional) and value is
    the default kwargs options to pass.
    :return:
    """
    if options is None:
        options = {}

    for value, raw_entries in config.items():
        entries = raw_entries if isinstance(raw_entries, list) else [raw_entries]
        for entry in entries:
            if isinstance(entry, dict) and "callable" in entry.keys():
                _process_callable_entry(entry.pop("callable"), rebulk, entry)
                continue
            entry_decl = _build_entry_decl(entry, options, value)

            for pattern_type in _pattern_types:
                patterns = entry_decl.get(pattern_type)
                if not patterns:
                    continue
                if not isinstance(patterns, list):
                    patterns = [patterns]
                patterns_entry_decl = dict(entry_decl)

                for pattern_type_to_remove in _pattern_types:
                    patterns_entry_decl.pop(pattern_type_to_remove, None)

                current_pattern_options = dict(options)
                current_pattern_options[None] = patterns_entry_decl

                load_patterns(rebulk, pattern_type, patterns, current_pattern_options)
