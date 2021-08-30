"""CSS selector parser."""
from __future__ import unicode_literals
import re
from . import util
from . import css_match as cm
from . import css_types as ct
from .util import SelectorSyntaxError

UNICODE_REPLACEMENT_CHAR = 0xFFFD

# Simple pseudo classes that take no parameters
PSEUDO_SIMPLE = {
    ":any-link",
    ":empty",
    ":first-child",
    ":first-of-type",
    ":in-range",
    ":out-of-range",
    ":last-child",
    ":last-of-type",
    ":link",
    ":only-child",
    ":only-of-type",
    ":root",
    ':checked',
    ':default',
    ':disabled',
    ':enabled',
    ':indeterminate',
    ':optional',
    ':placeholder-shown',
    ':read-only',
    ':read-write',
    ':required',
    ':scope',
    ':defined'
}

# Supported, simple pseudo classes that match nothing in the Soup Sieve environment
PSEUDO_SIMPLE_NO_MATCH = {
    ':active',
    ':current',
    ':focus',
    ':focus-visible',
    ':focus-within',
    ':future',
    ':host',
    ':hover',
    ':local-link',
    ':past',
    ':paused',
    ':playing',
    ':target',
    ':target-within',
    ':user-invalid',
    ':visited'
}

# Complex pseudo classes that take selector lists
PSEUDO_COMPLEX = {
    ':contains',
    ':has',
    ':is',
    ':matches',
    ':not',
    ':where'
}

PSEUDO_COMPLEX_NO_MATCH = {
    ':current',
    ':host',
    ':host-context'
}

# Complex pseudo classes that take very specific parameters and are handled special
PSEUDO_SPECIAL = {
    ':dir',
    ':lang',
    ':nth-child',
    ':nth-last-child',
    ':nth-last-of-type',
    ':nth-of-type'
}

PSEUDO_SUPPORTED = PSEUDO_SIMPLE | PSEUDO_SIMPLE_NO_MATCH | PSEUDO_COMPLEX | PSEUDO_COMPLEX_NO_MATCH | PSEUDO_SPECIAL

# Sub-patterns parts
# Whitespace
NEWLINE = r'(?:\r\n|(?!\r\n)[\n\f\r])'
WS = r'(?:[ \t]|{})'.format(NEWLINE)
# Comments
COMMENTS = r'(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)'
# Whitespace with comments included
WSC = r'(?:{ws}|{comments})'.format(ws=WS, comments=COMMENTS)
# CSS escapes
CSS_ESCAPES = r'(?:\\(?:[a-f0-9]{{1,6}}{ws}?|[^\r\n\f]|$))'.format(ws=WS)
CSS_STRING_ESCAPES = r'(?:\\(?:[a-f0-9]{{1,6}}{ws}?|[^\r\n\f]|$|{nl}))'.format(ws=WS, nl=NEWLINE)
# CSS Identifier
IDENTIFIER = r'''
(?:(?:-?(?:[^\x00-\x2f\x30-\x40\x5B-\x5E\x60\x7B-\x9f]|{esc})+|--)
(?:[^\x00-\x2c\x2e\x2f\x3A-\x40\x5B-\x5E\x60\x7B-\x9f]|{esc})*)
'''.format(esc=CSS_ESCAPES)
# `nth` content
NTH = r'(?:[-+])?(?:[0-9]+n?|n)(?:(?<=n){ws}*(?:[-+]){ws}*(?:[0-9]+))?'.format(ws=WSC)
# Value: quoted string or identifier
VALUE = r'''
(?:"(?:\\(?:.|{nl})|[^\\"\r\n\f]+)*?"|'(?:\\(?:.|{nl})|[^\\'\r\n\f]+)*?'|{ident}+)
'''.format(nl=NEWLINE, ident=IDENTIFIER)
# Attribute value comparison. `!=` is handled special as it is non-standard.
ATTR = r'''
(?:{ws}*(?P<cmp>[!~^|*$]?=){ws}*(?P<value>{value})(?:{ws}+(?P<case>[is]))?)?{ws}*\]
'''.format(ws=WSC, value=VALUE)

# Selector patterns
# IDs (`#id`)
PAT_ID = r'\#{ident}'.format(ident=IDENTIFIER)
# Classes (`.class`)
PAT_CLASS = r'\.{ident}'.format(ident=IDENTIFIER)
# Prefix:Tag (`prefix|tag`)
PAT_TAG = r'(?:(?:{ident}|\*)?\|)?(?:{ident}|\*)'.format(ident=IDENTIFIER)
# Attributes (`[attr]`, `[attr=value]`, etc.)
PAT_ATTR = r'\[{ws}*(?P<ns_attr>(?:(?:{ident}|\*)?\|)?{ident}){attr}'.format(ws=WSC, ident=IDENTIFIER, attr=ATTR)
# Pseudo class (`:pseudo-class`, `:pseudo-class(`)
PAT_PSEUDO_CLASS = r'(?P<name>:{ident})(?P<open>\({ws}*)?'.format(ws=WSC, ident=IDENTIFIER)
# Pseudo class special patterns. Matches `:pseudo-class(` for special case pseudo classes.
PAT_PSEUDO_CLASS_SPECIAL = r'(?P<name>:{ident})(?P<open>\({ws}*)'.format(ws=WSC, ident=IDENTIFIER)
# Custom pseudo class (`:--custom-pseudo`)
PAT_PSEUDO_CLASS_CUSTOM = r'(?P<name>:(?=--){ident})'.format(ident=IDENTIFIER)
# Closing pseudo group (`)`)
PAT_PSEUDO_CLOSE = r'{ws}*\)'.format(ws=WSC)
# Pseudo element (`::pseudo-element`)
PAT_PSEUDO_ELEMENT = r':{}'.format(PAT_PSEUDO_CLASS)
# At rule (`@page`, etc.) (not supported)
PAT_AT_RULE = r'@P{ident}'.format(ident=IDENTIFIER)
# Pseudo class `nth-child` (`:nth-child(an+b [of S]?)`, `:first-child`, etc.)
PAT_PSEUDO_NTH_CHILD = r'''
(?P<pseudo_nth_child>{name}
(?P<nth_child>{nth}|even|odd))(?:{wsc}*\)|(?P<of>{comments}*{ws}{wsc}*of{comments}*{ws}{wsc}*))
'''.format(name=PAT_PSEUDO_CLASS_SPECIAL, wsc=WSC, comments=COMMENTS, ws=WS, nth=NTH)
# Pseudo class `nth-of-type` (`:nth-of-type(an+b)`, `:first-of-type`, etc.)
PAT_PSEUDO_NTH_TYPE = r'''
(?P<pseudo_nth_type>{name}
(?P<nth_type>{nth}|even|odd)){ws}*\)
'''.format(name=PAT_PSEUDO_CLASS_SPECIAL, ws=WSC, nth=NTH)
# Pseudo class language (`:lang("*-de", en)`)
PAT_PSEUDO_LANG = r'{name}(?P<values>{value}(?:{ws}*,{ws}*{value})*){ws}*\)'.format(
    name=PAT_PSEUDO_CLASS_SPECIAL, ws=WSC, value=VALUE
)
# Pseudo class direction (`:dir(ltr)`)
PAT_PSEUDO_DIR = r'{name}(?P<dir>ltr|rtl){ws}*\)'.format(name=PAT_PSEUDO_CLASS_SPECIAL, ws=WSC)
# Combining characters (`>`, `~`, ` `, `+`, `,`)
PAT_COMBINE = r'{wsc}*?(?P<relation>[,+>~]|{ws}(?![,+>~])){wsc}*'.format(ws=WS, wsc=WSC)
# Extra: Contains (`:contains(text)`)
PAT_PSEUDO_CONTAINS = r'{name}(?P<values>{value}(?:{ws}*,{ws}*{value})*){ws}*\)'.format(
    name=PAT_PSEUDO_CLASS_SPECIAL, ws=WSC, value=VALUE
)

# Regular expressions
# CSS escape pattern
RE_CSS_ESC = re.compile(r'(?:(\\[a-f0-9]{{1,6}}{ws}?)|(\\[^\r\n\f])|(\\$))'.format(ws=WSC), re.I)
RE_CSS_STR_ESC = re.compile(
    r'(?:(\\[a-f0-9]{{1,6}}{ws}?)|(\\[^\r\n\f])|(\\$)|(\\{nl}))'.format(ws=WS, nl=NEWLINE), re.I
)
# Pattern to break up `nth` specifiers
RE_NTH = re.compile(
    r'(?P<s1>[-+])?(?P<a>[0-9]+n?|n)(?:(?<=n){ws}*(?P<s2>[-+]){ws}*(?P<b>[0-9]+))?'.format(ws=WSC),
    re.I
)
# Pattern to iterate multiple values.
RE_VALUES = re.compile(r'(?:(?P<value>{value})|(?P<split>{ws}*,{ws}*))'.format(ws=WSC, value=VALUE), re.X)
# Whitespace checks
RE_WS = re.compile(WS)
RE_WS_BEGIN = re.compile('^{}*'.format(WSC))
RE_WS_END = re.compile('{}*$'.format(WSC))
RE_CUSTOM = re.compile(r'^{}$'.format(PAT_PSEUDO_CLASS_CUSTOM), re.X)

# Constants
# List split token
COMMA_COMBINATOR = ','
# Relation token for descendant
WS_COMBINATOR = " "

# Parse flags
FLG_PSEUDO = 0x01
FLG_NOT = 0x02
FLG_RELATIVE = 0x04
FLG_DEFAULT = 0x08
FLG_HTML = 0x10
FLG_INDETERMINATE = 0x20
FLG_OPEN = 0x40
FLG_IN_RANGE = 0x80
FLG_OUT_OF_RANGE = 0x100

# Maximum cached patterns to store
_MAXCACHE = 500


@util.lru_cache(maxsize=_MAXCACHE)
def _cached_css_compile(pattern, namespaces, custom, flags):
    """Cached CSS compile."""

    custom_selectors = process_custom(custom)
    return cm.SoupSieve(
        pattern,
        CSSParser(pattern, custom=custom_selectors, flags=flags).process_selectors(),
        namespaces,
        custom,
        flags
    )


def _purge_cache():
    """Purge the cache."""

    _cached_css_compile.cache_clear()


def process_custom(custom):
    """Process custom."""

    custom_selectors = {}
    if custom is not None:
        for key, value in custom.items():
            name = util.lower(key)
            if RE_CUSTOM.match(name) is None:
                raise SelectorSyntaxError("The name '{}' is not a valid custom pseudo-class name".format(name))
            if name in custom_selectors:
                raise KeyError("The custom selector '{}' has already been registered".format(name))
            custom_selectors[css_unescape(name)] = value
    return custom_selectors


def css_unescape(content, string=False):
    """
    Unescape CSS value.

    Strings allow for spanning the value on multiple strings by escaping a new line.
    """

    def replace(m):
        """Replace with the appropriate substitute."""

        if m.group(1):
            codepoint = int(m.group(1)[1:], 16)
            if codepoint == 0:
                codepoint = UNICODE_REPLACEMENT_CHAR
            value = util.uchr(codepoint)
        elif m.group(2):
            value = m.group(2)[1:]
        elif m.group(3):
            value = '\ufffd'
        else:
            value = ''

        return value

    return (RE_CSS_ESC if not string else RE_CSS_STR_ESC).sub(replace, content)


def escape(ident):
    """Escape identifier."""

    string = []
    length = len(ident)
    start_dash = length > 0 and ident[0] == '-'
    if length == 1 and start_dash:
        # Need to escape identifier that is a single `-` with no other characters
        string.append('\\{}'.format(ident))
    else:
        for index, c in enumerate(ident):
            codepoint = util.uord(c)
            if codepoint == 0x00:
                string.append('\ufffd')
            elif (0x01 <= codepoint <= 0x1F) or codepoint == 0x7F:
                string.append('\\{:x} '.format(codepoint))
            elif (index == 0 or (start_dash and index == 1)) and (0x30 <= codepoint <= 0x39):
                string.append('\\{:x} '.format(codepoint))
            elif (
                codepoint in (0x2D, 0x5F) or codepoint >= 0x80 or (0x30 <= codepoint <= 0x39) or
                (0x30 <= codepoint <= 0x39) or (0x41 <= codepoint <= 0x5A) or (0x61 <= codepoint <= 0x7A)
            ):
                string.append(c)
            else:
                string.append('\\{}'.format(c))
    return ''.join(string)


class SelectorPattern(object):
    """Selector pattern."""

    def __init__(self, name, pattern):
        """Initialize."""

        self.name = name
        self.re_pattern = re.compile(pattern, re.I | re.X | re.U)

    def get_name(self):
        """Get name."""

        return self.name

    def enabled(self, flags):
        """Enabled."""

        return True

    def match(self, selector, index):
        """Match the selector."""

        return self.re_pattern.match(selector, index)


class SpecialPseudoPattern(SelectorPattern):
    """Selector pattern."""

    def __init__(self, patterns):
        """Initialize."""

        self.patterns = {}
        for p in patterns:
            name = p[0]
            pattern = SelectorPattern(name, p[2])
            for pseudo in p[1]:
                self.patterns[pseudo] = pattern

        self.matched_name = None
        self.re_pseudo_name = re.compile(PAT_PSEUDO_CLASS_SPECIAL, re.I | re.X | re.U)

    def get_name(self):
        """Get name."""

        return self.matched_name.get_name()

    def enabled(self, flags):
        """Enabled."""

        return True

    def match(self, selector, index):
        """Match the selector."""

        pseudo = None
        m = self.re_pseudo_name.match(selector, index)
        if m:
            name = util.lower(css_unescape(m.group('name')))
            pattern = self.patterns.get(name)
            if pattern:
                pseudo = pattern.match(selector, index)
                if pseudo:
                    self.matched_name = pattern

        return pseudo


class _Selector(object):
    """
    Intermediate selector class.

    This stores selector data for a compound selector as we are acquiring them.
    Once we are done collecting the data for a compound selector, we freeze
    the data in an object that can be pickled and hashed.
    """

    def __init__(self, **kwargs):
        """Initialize."""

        self.tag = kwargs.get('tag', None)
        self.ids = kwargs.get('ids', [])
        self.classes = kwargs.get('classes', [])
        self.attributes = kwargs.get('attributes', [])
        self.nth = kwargs.get('nth', [])
        self.selectors = kwargs.get('selectors', [])
        self.relations = kwargs.get('relations', [])
        self.rel_type = kwargs.get('rel_type', None)
        self.contains = kwargs.get('contains', [])
        self.lang = kwargs.get('lang', [])
        self.flags = kwargs.get('flags', 0)
        self.no_match = kwargs.get('no_match', False)

    def _freeze_relations(self, relations):
        """Freeze relation."""

        if relations:
            sel = relations[0]
            sel.relations.extend(relations[1:])
            return ct.SelectorList([sel.freeze()])
        else:
            return ct.SelectorList()

    def freeze(self):
        """Freeze self."""

        if self.no_match:
            return ct.SelectorNull()
        else:
            return ct.Selector(
                self.tag,
                tuple(self.ids),
                tuple(self.classes),
                tuple(self.attributes),
                tuple(self.nth),
                tuple(self.selectors),
                self._freeze_relations(self.relations),
                self.rel_type,
                tuple(self.contains),
                tuple(self.lang),
                self.flags
            )

    def __str__(self):  # pragma: no cover
        """String representation."""

        return (
            '_Selector(tag={!r}, ids={!r}, classes={!r}, attributes={!r}, nth={!r}, selectors={!r}, '
            'relations={!r}, rel_type={!r}, contains={!r}, lang={!r}, flags={!r}, no_match={!r})'
        ).format(
            self.tag, self.ids, self.classes, self.attributes, self.nth, self.selectors,
            self.relations, self.rel_type, self.contains, self.lang, self.flags, self.no_match
        )

    __repr__ = __str__


class CSSParser(object):
    """Parse CSS selectors."""

    css_tokens = (
        SelectorPattern("pseudo_close", PAT_PSEUDO_CLOSE),
        SpecialPseudoPattern(
            (
                ("pseudo_contains", (':contains',), PAT_PSEUDO_CONTAINS),
                ("pseudo_nth_child", (':nth-child', ':nth-last-child'), PAT_PSEUDO_NTH_CHILD),
                ("pseudo_nth_type", (':nth-of-type', ':nth-last-of-type'), PAT_PSEUDO_NTH_TYPE),
                ("pseudo_lang", (':lang',), PAT_PSEUDO_LANG),
                ("pseudo_dir", (':dir',), PAT_PSEUDO_DIR)
            )
        ),
        SelectorPattern("pseudo_class_custom", PAT_PSEUDO_CLASS_CUSTOM),
        SelectorPattern("pseudo_class", PAT_PSEUDO_CLASS),
        SelectorPattern("pseudo_element", PAT_PSEUDO_ELEMENT),
        SelectorPattern("at_rule", PAT_AT_RULE),
        SelectorPattern("id", PAT_ID),
        SelectorPattern("class", PAT_CLASS),
        SelectorPattern("tag", PAT_TAG),
        SelectorPattern("attribute", PAT_ATTR),
        SelectorPattern("combine", PAT_COMBINE)
    )

    def __init__(self, selector, custom=None, flags=0):
        """Initialize."""

        self.pattern = selector.replace('\x00', '\ufffd')
        self.flags = flags
        self.debug = self.flags & util.DEBUG
        self.custom = {} if custom is None else custom

    def parse_attribute_selector(self, sel, m, has_selector):
        """Create attribute selector from the returned regex match."""

        inverse = False
        op = m.group('cmp')
        case = util.lower(m.group('case')) if m.group('case') else None
        parts = [css_unescape(a) for a in m.group('ns_attr').split('|')]
        ns = ''
        is_type = False
        pattern2 = None
        if len(parts) > 1:
            ns = parts[0]
            attr = parts[1]
        else:
            attr = parts[0]
        if case:
            flags = re.I if case == 'i' else 0
        elif util.lower(attr) == 'type':
            flags = re.I
            is_type = True
        else:
            flags = 0

        if op:
            if m.group('value').startswith(('"', "'")):
                value = css_unescape(m.group('value')[1:-1], True)
            else:
                value = css_unescape(m.group('value'))
        else:
            value = None
        if not op:
            # Attribute name
            pattern = None
        elif op.startswith('^'):
            # Value start with
            pattern = re.compile(r'^%s.*' % re.escape(value), flags)
        elif op.startswith('$'):
            # Value ends with
            pattern = re.compile(r'.*?%s$' % re.escape(value), flags)
        elif op.startswith('*'):
            # Value contains
            pattern = re.compile(r'.*?%s.*' % re.escape(value), flags)
        elif op.startswith('~'):
            # Value contains word within space separated list
            # `~=` should match nothing if it is empty or contains whitespace,
            # so if either of these cases is present, use `[^\s\S]` which cannot be matched.
            value = r'[^\s\S]' if not value or RE_WS.search(value) else re.escape(value)
            pattern = re.compile(r'.*?(?:(?<=^)|(?<=[ \t\r\n\f]))%s(?=(?:[ \t\r\n\f]|$)).*' % value, flags)
        elif op.startswith('|'):
            # Value starts with word in dash separated list
            pattern = re.compile(r'^%s(?:-.*)?$' % re.escape(value), flags)
        else:
            # Value matches
            pattern = re.compile(r'^%s$' % re.escape(value), flags)
            if op.startswith('!'):
                # Equivalent to `:not([attr=value])`
                inverse = True
        if is_type and pattern:
            pattern2 = re.compile(pattern.pattern)

        # Append the attribute selector
        sel_attr = ct.SelectorAttribute(attr, ns, pattern, pattern2)
        if inverse:
            # If we are using `!=`, we need to nest the pattern under a `:not()`.
            sub_sel = _Selector()
            sub_sel.attributes.append(sel_attr)
            not_list = ct.SelectorList([sub_sel.freeze()], True, False)
            sel.selectors.append(not_list)
        else:
            sel.attributes.append(sel_attr)

        has_selector = True
        return has_selector

    def parse_tag_pattern(self, sel, m, has_selector):
        """Parse tag pattern from regex match."""

        parts = [css_unescape(x) for x in m.group(0).split('|')]
        if len(parts) > 1:
            prefix = parts[0]
            tag = parts[1]
        else:
            tag = parts[0]
            prefix = None
        sel.tag = ct.SelectorTag(tag, prefix)
        has_selector = True
        return has_selector

    def parse_pseudo_class_custom(self, sel, m, has_selector):
        """
        Parse custom pseudo class alias.

        Compile custom selectors as we need them. When compiling a custom selector,
        set it to `None` in the dictionary so we can avoid an infinite loop.
        """

        pseudo = util.lower(css_unescape(m.group('name')))
        selector = self.custom.get(pseudo)
        if selector is None:
            raise SelectorSyntaxError(
                "Undefined custom selector '{}' found at postion {}".format(pseudo, m.end(0)),
                self.pattern,
                m.end(0)
            )

        if not isinstance(selector, ct.SelectorList):
            self.custom[pseudo] = None
            selector = CSSParser(
                selector, custom=self.custom, flags=self.flags
            ).process_selectors(flags=FLG_PSEUDO)
            self.custom[pseudo] = selector

        sel.selectors.append(selector)
        has_selector = True
        return has_selector

    def parse_pseudo_class(self, sel, m, has_selector, iselector, is_html):
        """Parse pseudo class."""

        complex_pseudo = False
        pseudo = util.lower(css_unescape(m.group('name')))
        if m.group('open'):
            complex_pseudo = True
        if complex_pseudo and pseudo in PSEUDO_COMPLEX:
            has_selector = self.parse_pseudo_open(sel, pseudo, has_selector, iselector, m.end(0))
        elif not complex_pseudo and pseudo in PSEUDO_SIMPLE:
            if pseudo == ':root':
                sel.flags |= ct.SEL_ROOT
            elif pseudo == ':defined':
                sel.flags |= ct.SEL_DEFINED
                is_html = True
            elif pseudo == ':scope':
                sel.flags |= ct.SEL_SCOPE
            elif pseudo == ':empty':
                sel.flags |= ct.SEL_EMPTY
            elif pseudo in (':link', ':any-link'):
                sel.selectors.append(CSS_LINK)
            elif pseudo == ':checked':
                sel.selectors.append(CSS_CHECKED)
            elif pseudo == ':default':
                sel.selectors.append(CSS_DEFAULT)
            elif pseudo == ':indeterminate':
                sel.selectors.append(CSS_INDETERMINATE)
            elif pseudo == ":disabled":
                sel.selectors.append(CSS_DISABLED)
            elif pseudo == ":enabled":
                sel.selectors.append(CSS_ENABLED)
            elif pseudo == ":required":
                sel.selectors.append(CSS_REQUIRED)
            elif pseudo == ":optional":
                sel.selectors.append(CSS_OPTIONAL)
            elif pseudo == ":read-only":
                sel.selectors.append(CSS_READ_ONLY)
            elif pseudo == ":read-write":
                sel.selectors.append(CSS_READ_WRITE)
            elif pseudo == ":in-range":
                sel.selectors.append(CSS_IN_RANGE)
            elif pseudo == ":out-of-range":
                sel.selectors.append(CSS_OUT_OF_RANGE)
            elif pseudo == ":placeholder-shown":
                sel.selectors.append(CSS_PLACEHOLDER_SHOWN)
            elif pseudo == ':first-child':
                sel.nth.append(ct.SelectorNth(1, False, 0, False, False, ct.SelectorList()))
            elif pseudo == ':last-child':
                sel.nth.append(ct.SelectorNth(1, False, 0, False, True, ct.SelectorList()))
            elif pseudo == ':first-of-type':
                sel.nth.append(ct.SelectorNth(1, False, 0, True, False, ct.SelectorList()))
            elif pseudo == ':last-of-type':
                sel.nth.append(ct.SelectorNth(1, False, 0, True, True, ct.SelectorList()))
            elif pseudo == ':only-child':
                sel.nth.extend(
                    [
                        ct.SelectorNth(1, False, 0, False, False, ct.SelectorList()),
                        ct.SelectorNth(1, False, 0, False, True, ct.SelectorList())
                    ]
                )
            elif pseudo == ':only-of-type':
                sel.nth.extend(
                    [
                        ct.SelectorNth(1, False, 0, True, False, ct.SelectorList()),
                        ct.SelectorNth(1, False, 0, True, True, ct.SelectorList())
                    ]
                )
            has_selector = True
        elif complex_pseudo and pseudo in PSEUDO_COMPLEX_NO_MATCH:
            self.parse_selectors(iselector, m.end(0), FLG_PSEUDO | FLG_OPEN)
            sel.no_match = True
            has_selector = True
        elif not complex_pseudo and pseudo in PSEUDO_SIMPLE_NO_MATCH:
            sel.no_match = True
            has_selector = True
        elif pseudo in PSEUDO_SUPPORTED:
            raise SelectorSyntaxError(
                "Invalid syntax for pseudo class '{}'".format(pseudo),
                self.pattern,
                m.start(0)
            )
        else:
            raise NotImplementedError(
                "'{}' pseudo-class is not implemented at this time".format(pseudo)
            )

        return has_selector, is_html

    def parse_pseudo_nth(self, sel, m, has_selector, iselector):
        """Parse `nth` pseudo."""

        mdict = m.groupdict()
        if mdict.get('pseudo_nth_child'):
            postfix = '_child'
        else:
            postfix = '_type'
        mdict['name'] = util.lower(css_unescape(mdict['name']))
        content = util.lower(mdict.get('nth' + postfix))
        if content == 'even':
            # 2n
            s1 = 2
            s2 = 0
            var = True
        elif content == 'odd':
            # 2n+1
            s1 = 2
            s2 = 1
            var = True
        else:
            nth_parts = RE_NTH.match(content)
            s1 = '-' if nth_parts.group('s1') and nth_parts.group('s1') == '-' else ''
            a = nth_parts.group('a')
            var = a.endswith('n')
            if a.startswith('n'):
                s1 += '1'
            elif var:
                s1 += a[:-1]
            else:
                s1 += a
            s2 = '-' if nth_parts.group('s2') and nth_parts.group('s2') == '-' else ''
            if nth_parts.group('b'):
                s2 += nth_parts.group('b')
            else:
                s2 = '0'
            s1 = int(s1, 10)
            s2 = int(s2, 10)

        pseudo_sel = mdict['name']
        if postfix == '_child':
            if m.group('of'):
                # Parse the rest of `of S`.
                nth_sel = self.parse_selectors(iselector, m.end(0), FLG_PSEUDO | FLG_OPEN)
            else:
                # Use default `*|*` for `of S`.
                nth_sel = CSS_NTH_OF_S_DEFAULT
            if pseudo_sel == ':nth-child':
                sel.nth.append(ct.SelectorNth(s1, var, s2, False, False, nth_sel))
            elif pseudo_sel == ':nth-last-child':
                sel.nth.append(ct.SelectorNth(s1, var, s2, False, True, nth_sel))
        else:
            if pseudo_sel == ':nth-of-type':
                sel.nth.append(ct.SelectorNth(s1, var, s2, True, False, ct.SelectorList()))
            elif pseudo_sel == ':nth-last-of-type':
                sel.nth.append(ct.SelectorNth(s1, var, s2, True, True, ct.SelectorList()))
        has_selector = True
        return has_selector

    def parse_pseudo_open(self, sel, name, has_selector, iselector, index):
        """Parse pseudo with opening bracket."""

        flags = FLG_PSEUDO | FLG_OPEN
        if name == ':not':
            flags |= FLG_NOT
        if name == ':has':
            flags |= FLG_RELATIVE

        sel.selectors.append(self.parse_selectors(iselector, index, flags))
        has_selector = True
        return has_selector

    def parse_has_combinator(self, sel, m, has_selector, selectors, rel_type, index):
        """Parse combinator tokens."""

        combinator = m.group('relation').strip()
        if not combinator:
            combinator = WS_COMBINATOR
        if combinator == COMMA_COMBINATOR:
            if not has_selector:
                # If we've not captured any selector parts, the comma is either at the beginning of the pattern
                # or following another comma, both of which are unexpected. Commas must split selectors.
                raise SelectorSyntaxError(
                    "The combinator '{}' at postion {}, must have a selector before it".format(combinator, index),
                    self.pattern,
                    index
                )
            sel.rel_type = rel_type
            selectors[-1].relations.append(sel)
            rel_type = ":" + WS_COMBINATOR
            selectors.append(_Selector())
        else:
            if has_selector:
                # End the current selector and associate the leading combinator with this selector.
                sel.rel_type = rel_type
                selectors[-1].relations.append(sel)
            elif rel_type[1:] != WS_COMBINATOR:
                # It's impossible to have two whitespace combinators after each other as the patterns
                # will gobble up trailing whitespace. It is also impossible to have a whitespace
                # combinator after any other kind for the same reason. But we could have
                # multiple non-whitespace combinators. So if the current combinator is not a whitespace,
                # then we've hit the multiple combinator case, so we should fail.
                raise SelectorSyntaxError(
                    'The multiple combinators at position {}'.format(index),
                    self.pattern,
                    index
                )
            # Set the leading combinator for the next selector.
            rel_type = ':' + combinator
        sel = _Selector()

        has_selector = False
        return has_selector, sel, rel_type

    def parse_combinator(self, sel, m, has_selector, selectors, relations, is_pseudo, index):
        """Parse combinator tokens."""

        combinator = m.group('relation').strip()
        if not combinator:
            combinator = WS_COMBINATOR
        if not has_selector:
            raise SelectorSyntaxError(
                "The combinator '{}' at postion {}, must have a selector before it".format(combinator, index),
                self.pattern,
                index
            )

        if combinator == COMMA_COMBINATOR:
            if not sel.tag and not is_pseudo:
                # Implied `*`
                sel.tag = ct.SelectorTag('*', None)
            sel.relations.extend(relations)
            selectors.append(sel)
            del relations[:]
        else:
            sel.relations.extend(relations)
            sel.rel_type = combinator
            del relations[:]
            relations.append(sel)
        sel = _Selector()

        has_selector = False
        return has_selector, sel

    def parse_class_id(self, sel, m, has_selector):
        """Parse HTML classes and ids."""

        selector = m.group(0)
        if selector.startswith('.'):
            sel.classes.append(css_unescape(selector[1:]))
        else:
            sel.ids.append(css_unescape(selector[1:]))
        has_selector = True
        return has_selector

    def parse_pseudo_contains(self, sel, m, has_selector):
        """Parse contains."""

        values = m.group('values')
        patterns = []
        for token in RE_VALUES.finditer(values):
            if token.group('split'):
                continue
            value = token.group('value')
            if value.startswith(("'", '"')):
                value = css_unescape(value[1:-1], True)
            else:
                value = css_unescape(value)
            patterns.append(value)
        sel.contains.append(ct.SelectorContains(tuple(patterns)))
        has_selector = True
        return has_selector

    def parse_pseudo_lang(self, sel, m, has_selector):
        """Parse pseudo language."""

        values = m.group('values')
        patterns = []
        for token in RE_VALUES.finditer(values):
            if token.group('split'):
                continue
            value = token.group('value')
            if value.startswith(('"', "'")):
                parts = css_unescape(value[1:-1], True).split('-')
            else:
                parts = css_unescape(value).split('-')

            new_parts = []
            first = True
            for part in parts:
                if part == '*' and first:
                    new_parts.append('(?!x\b)[a-z0-9]+?')
                elif part != '*':
                    new_parts.append(('' if first else '(-(?!x\b)[a-z0-9]+)*?\\-') + re.escape(part))
                if first:
                    first = False
            patterns.append(re.compile(r'^{}(?:-.*)?$'.format(''.join(new_parts)), re.I))
        sel.lang.append(ct.SelectorLang(patterns))
        has_selector = True

        return has_selector

    def parse_pseudo_dir(self, sel, m, has_selector):
        """Parse pseudo direction."""

        value = ct.SEL_DIR_LTR if util.lower(m.group('dir')) == 'ltr' else ct.SEL_DIR_RTL
        sel.flags |= value
        has_selector = True
        return has_selector

    def parse_selectors(self, iselector, index=0, flags=0):
        """Parse selectors."""

        sel = _Selector()
        selectors = []
        has_selector = False
        closed = False
        relations = []
        rel_type = ":" + WS_COMBINATOR
        is_open = bool(flags & FLG_OPEN)
        is_pseudo = bool(flags & FLG_PSEUDO)
        is_relative = bool(flags & FLG_RELATIVE)
        is_not = bool(flags & FLG_NOT)
        is_html = bool(flags & FLG_HTML)
        is_default = bool(flags & FLG_DEFAULT)
        is_indeterminate = bool(flags & FLG_INDETERMINATE)
        is_in_range = bool(flags & FLG_IN_RANGE)
        is_out_of_range = bool(flags & FLG_OUT_OF_RANGE)

        if self.debug:  # pragma: no cover
            if is_pseudo:
                print('    is_pseudo: True')
            if is_open:
                print('    is_open: True')
            if is_relative:
                print('    is_relative: True')
            if is_not:
                print('    is_not: True')
            if is_html:
                print('    is_html: True')
            if is_default:
                print('    is_default: True')
            if is_indeterminate:
                print('    is_indeterminate: True')
            if is_in_range:
                print('    is_in_range: True')
            if is_out_of_range:
                print('    is_out_of_range: True')

        if is_relative:
            selectors.append(_Selector())

        try:
            while True:
                key, m = next(iselector)

                # Handle parts
                if key == "at_rule":
                    raise NotImplementedError("At-rules found at position {}".format(m.start(0)))
                elif key == 'pseudo_class_custom':
                    has_selector = self.parse_pseudo_class_custom(sel, m, has_selector)
                elif key == 'pseudo_class':
                    has_selector, is_html = self.parse_pseudo_class(sel, m, has_selector, iselector, is_html)
                elif key == 'pseudo_element':
                    raise NotImplementedError("Psuedo-element found at position {}".format(m.start(0)))
                elif key == 'pseudo_contains':
                    has_selector = self.parse_pseudo_contains(sel, m, has_selector)
                elif key in ('pseudo_nth_type', 'pseudo_nth_child'):
                    has_selector = self.parse_pseudo_nth(sel, m, has_selector, iselector)
                elif key == 'pseudo_lang':
                    has_selector = self.parse_pseudo_lang(sel, m, has_selector)
                elif key == 'pseudo_dir':
                    has_selector = self.parse_pseudo_dir(sel, m, has_selector)
                    # Currently only supports HTML
                    is_html = True
                elif key == 'pseudo_close':
                    if not has_selector:
                        raise SelectorSyntaxError(
                            "Expected a selector at postion {}".format(m.start(0)),
                            self.pattern,
                            m.start(0)
                        )
                    if is_open:
                        closed = True
                        break
                    else:
                        raise SelectorSyntaxError(
                            "Unmatched pseudo-class close at postion {}".format(m.start(0)),
                            self.pattern,
                            m.start(0)
                        )
                elif key == 'combine':
                    if is_relative:
                        has_selector, sel, rel_type = self.parse_has_combinator(
                            sel, m, has_selector, selectors, rel_type, index
                        )
                    else:
                        has_selector, sel = self.parse_combinator(
                            sel, m, has_selector, selectors, relations, is_pseudo, index
                        )
                elif key == 'attribute':
                    has_selector = self.parse_attribute_selector(sel, m, has_selector)
                elif key == 'tag':
                    if has_selector:
                        raise SelectorSyntaxError(
                            "Tag name found at position {} instead of at the start".format(m.start(0)),
                            self.pattern,
                            m.start(0)
                        )
                    has_selector = self.parse_tag_pattern(sel, m, has_selector)
                elif key in ('class', 'id'):
                    has_selector = self.parse_class_id(sel, m, has_selector)

                index = m.end(0)
        except StopIteration:
            pass

        if is_open and not closed:
            raise SelectorSyntaxError(
                "Unclosed pseudo-class at position {}".format(index),
                self.pattern,
                index
            )

        if has_selector:
            if not sel.tag and not is_pseudo:
                # Implied `*`
                sel.tag = ct.SelectorTag('*', None)
            if is_relative:
                sel.rel_type = rel_type
                selectors[-1].relations.append(sel)
            else:
                sel.relations.extend(relations)
                del relations[:]
                selectors.append(sel)
        else:
            # We will always need to finish a selector when `:has()` is used as it leads with combining.
            raise SelectorSyntaxError(
                'Expected a selector at position {}'.format(index),
                self.pattern,
                index
            )

        # Some patterns require additional logic, such as default. We try to make these the
        # last pattern, and append the appropriate flag to that selector which communicates
        # to the matcher what additional logic is required.
        if is_default:
            selectors[-1].flags = ct.SEL_DEFAULT
        if is_indeterminate:
            selectors[-1].flags = ct.SEL_INDETERMINATE
        if is_in_range:
            selectors[-1].flags = ct.SEL_IN_RANGE
        if is_out_of_range:
            selectors[-1].flags = ct.SEL_OUT_OF_RANGE

        return ct.SelectorList([s.freeze() for s in selectors], is_not, is_html)

    def selector_iter(self, pattern):
        """Iterate selector tokens."""

        # Ignore whitespace and comments at start and end of pattern
        m = RE_WS_BEGIN.search(pattern)
        index = m.end(0) if m else 0
        m = RE_WS_END.search(pattern)
        end = (m.start(0) - 1) if m else (len(pattern) - 1)

        if self.debug:  # pragma: no cover
            print('## PARSING: {!r}'.format(pattern))
        while index <= end:
            m = None
            for v in self.css_tokens:
                if not v.enabled(self.flags):  # pragma: no cover
                    continue
                m = v.match(pattern, index)
                if m:
                    name = v.get_name()
                    if self.debug:  # pragma: no cover
                        print("TOKEN: '{}' --> {!r} at position {}".format(name, m.group(0), m.start(0)))
                    index = m.end(0)
                    yield name, m
                    break
            if m is None:
                c = pattern[index]
                # If the character represents the start of one of the known selector types,
                # throw an exception mentioning that the known selector type is in error;
                # otherwise, report the invalid character.
                if c == '[':
                    msg = "Malformed attribute selector at position {}".format(index)
                elif c == '.':
                    msg = "Malformed class selector at position {}".format(index)
                elif c == '#':
                    msg = "Malformed id selector at position {}".format(index)
                elif c == ':':
                    msg = "Malformed pseudo-class selector at position {}".format(index)
                else:
                    msg = "Invalid character {!r} position {}".format(c, index)
                raise SelectorSyntaxError(msg, self.pattern, index)
        if self.debug:  # pragma: no cover
            print('## END PARSING')

    def process_selectors(self, index=0, flags=0):
        """Process selectors."""

        return self.parse_selectors(self.selector_iter(self.pattern), index, flags)


# Precompile CSS selector lists for pseudo-classes (additional logic may be required beyond the pattern)
# A few patterns are order dependent as they use patterns previous compiled.

# CSS pattern for `:link` and `:any-link`
CSS_LINK = CSSParser(
    'html|*:is(a, area, link)[href]'
).process_selectors(flags=FLG_PSEUDO | FLG_HTML)
# CSS pattern for `:checked`
CSS_CHECKED = CSSParser(
    '''
    html|*:is(input[type=checkbox], input[type=radio])[checked],
    html|select > html|option[selected]
    '''
).process_selectors(flags=FLG_PSEUDO | FLG_HTML)
# CSS pattern for `:default` (must compile CSS_CHECKED first)
CSS_DEFAULT = CSSParser(
    '''
    :checked,

    /*
    This pattern must be at the end.
    Special logic is applied to the last selector.
    */
    html|form html|*:is(button, input)[type="submit"]
    '''
).process_selectors(flags=FLG_PSEUDO | FLG_HTML | FLG_DEFAULT)
# CSS pattern for `:indeterminate`
CSS_INDETERMINATE = CSSParser(
    '''
    html|input[type="checkbox"][indeterminate],
    html|input[type="radio"]:is(:not([name]), [name=""]):not([checked]),
    html|progress:not([value]),

    /*
    This pattern must be at the end.
    Special logic is applied to the last selector.
    */
    html|input[type="radio"][name][name!='']:not([checked])
    '''
).process_selectors(flags=FLG_PSEUDO | FLG_HTML | FLG_INDETERMINATE)
# CSS pattern for `:disabled`
CSS_DISABLED = CSSParser(
    '''
    html|*:is(input[type!=hidden], button, select, textarea, fieldset, optgroup, option, fieldset)[disabled],
    html|optgroup[disabled] > html|option,
    html|fieldset[disabled] > html|*:is(input[type!=hidden], button, select, textarea, fieldset),
    html|fieldset[disabled] >
        html|*:not(legend:nth-of-type(1)) html|*:is(input[type!=hidden], button, select, textarea, fieldset)
    '''
).process_selectors(flags=FLG_PSEUDO | FLG_HTML)
# CSS pattern for `:enabled`
CSS_ENABLED = CSSParser(
    '''
    html|*:is(input[type!=hidden], button, select, textarea, fieldset, optgroup, option, fieldset):not(:disabled)
    '''
).process_selectors(flags=FLG_PSEUDO | FLG_HTML)
# CSS pattern for `:required`
CSS_REQUIRED = CSSParser(
    'html|*:is(input, textarea, select)[required]'
).process_selectors(flags=FLG_PSEUDO | FLG_HTML)
# CSS pattern for `:optional`
CSS_OPTIONAL = CSSParser(
    'html|*:is(input, textarea, select):not([required])'
).process_selectors(flags=FLG_PSEUDO | FLG_HTML)
# CSS pattern for `:placeholder-shown`
CSS_PLACEHOLDER_SHOWN = CSSParser(
    '''
    html|*:is(
        input:is(
            :not([type]),
            [type=""],
            [type=text],
            [type=search],
            [type=url],
            [type=tel],
            [type=email],
            [type=password],
            [type=number]
        ),
        textarea
    )[placeholder][placeholder!='']
    '''
).process_selectors(flags=FLG_PSEUDO | FLG_HTML)
# CSS pattern default for `:nth-child` "of S" feature
CSS_NTH_OF_S_DEFAULT = CSSParser(
    '*|*'
).process_selectors(flags=FLG_PSEUDO)
# CSS pattern for `:read-write` (CSS_DISABLED must be compiled first)
CSS_READ_WRITE = CSSParser(
    '''
    html|*:is(
        textarea,
        input:is(
            :not([type]),
            [type=""],
            [type=text],
            [type=search],
            [type=url],
            [type=tel],
            [type=email],
            [type=number],
            [type=password],
            [type=date],
            [type=datetime-local],
            [type=month],
            [type=time],
            [type=week]
        )
    ):not([readonly], :disabled),
    html|*:is([contenteditable=""], [contenteditable="true" i])
    '''
).process_selectors(flags=FLG_PSEUDO | FLG_HTML)
# CSS pattern for `:read-only`
CSS_READ_ONLY = CSSParser(
    '''
    html|*:not(:read-write)
    '''
).process_selectors(flags=FLG_PSEUDO | FLG_HTML)
# CSS pattern for `:in-range`
CSS_IN_RANGE = CSSParser(
    '''
    html|input:is(
        [type="date"],
        [type="month"],
        [type="week"],
        [type="time"],
        [type="datetime-local"],
        [type="number"],
        [type="range"]
    ):is(
        [min],
        [max]
    )
    '''
).process_selectors(flags=FLG_PSEUDO | FLG_IN_RANGE | FLG_HTML)
# CSS pattern for `:out-of-range`
CSS_OUT_OF_RANGE = CSSParser(
    '''
    html|input:is(
        [type="date"],
        [type="month"],
        [type="week"],
        [type="time"],
        [type="datetime-local"],
        [type="number"],
        [type="range"]
    ):is(
        [min],
        [max]
    )
    '''
).process_selectors(flags=FLG_PSEUDO | FLG_OUT_OF_RANGE | FLG_HTML)
