import sys
import unicodedata
from collections import defaultdict


def is_lval(t):
    """Does not chceck whether t is not resticted or internal"""
    if not t:
        return False
    i = iter(t)
    if i.next() not in IDENTIFIER_START:
        return False
    return all(e in IDENTIFIER_PART for e in i)


def is_valid_lval(t):
    """Checks whether t is valid JS identifier name (no keyword like var, function, if etc)
    Also returns false on internal"""
    if not is_internal(t) and is_lval(t) and t not in RESERVED_NAMES:
        return True
    return False


def is_plval(t):
    return t.startswith('PyJsLval')


def is_marker(t):
    return t.startswith('PyJsMarker') or t.startswith('PyJsConstant')


def is_internal(t):
    return is_plval(t) or is_marker(t) or t == 'var'  # var is a scope var


def is_property_accessor(t):
    return '[' in t or '.' in t


def is_reserved(t):
    return t in RESERVED_NAMES


#http://stackoverflow.com/questions/14245893/efficiently-list-all-characters-in-a-given-unicode-category
BOM = u'\uFEFF'
ZWJ = u'\u200D'
ZWNJ = u'\u200C'
TAB = u'\u0009'
VT = u'\u000B'
FF = u'\u000C'
SP = u'\u0020'
NBSP = u'\u00A0'
LF = u'\u000A'
CR = u'\u000D'
LS = u'\u2028'
PS = u'\u2029'

U_CATEGORIES = defaultdict(list)  # Thank you Martijn Pieters!
for c in map(unichr, range(sys.maxunicode + 1)):
    U_CATEGORIES[unicodedata.category(c)].append(c)

UNICODE_LETTER = set(U_CATEGORIES['Lu'] + U_CATEGORIES['Ll'] +
                     U_CATEGORIES['Lt'] + U_CATEGORIES['Lm'] +
                     U_CATEGORIES['Lo'] + U_CATEGORIES['Nl'])
UNICODE_COMBINING_MARK = set(U_CATEGORIES['Mn'] + U_CATEGORIES['Mc'])
UNICODE_DIGIT = set(U_CATEGORIES['Nd'])
UNICODE_CONNECTOR_PUNCTUATION = set(U_CATEGORIES['Pc'])
IDENTIFIER_START = UNICODE_LETTER.union(
    {'$', '_'})  # and some fucking unicode escape sequence
IDENTIFIER_PART = IDENTIFIER_START.union(UNICODE_COMBINING_MARK).union(
    UNICODE_DIGIT).union(UNICODE_CONNECTOR_PUNCTUATION).union({ZWJ, ZWNJ})
USP = U_CATEGORIES['Zs']
KEYWORD = {
    'break', 'do', 'instanceof', 'typeof', 'case', 'else', 'new', 'var',
    'catch', 'finally', 'return', 'void', 'continue', 'for', 'switch', 'while',
    'debugger', 'function', 'this', 'with', 'default', 'if', 'throw', 'delete',
    'in', 'try'
}

FUTURE_RESERVED_WORD = {
    'class', 'enum', 'extends', 'super', 'const', 'export', 'import'
}
RESERVED_NAMES = KEYWORD.union(FUTURE_RESERVED_WORD).union(
    {'null', 'false', 'true'})

WHITE = {TAB, VT, FF, SP, NBSP, BOM}.union(USP)
LINE_TERMINATOR = {LF, CR, LS, PS}
LLINE_TERMINATOR = list(LINE_TERMINATOR)
x = ''.join(WHITE) + ''.join(LINE_TERMINATOR)
SPACE = WHITE.union(LINE_TERMINATOR)
LINE_TERMINATOR_SEQUENCE = LINE_TERMINATOR.union({CR + LF})
