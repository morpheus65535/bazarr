from string import ascii_lowercase, digits
##################################
StringName = u'PyJsConstantString%d_'
NumberName = u'PyJsConstantNumber%d_'
RegExpName = u'PyJsConstantRegExp%d_'
##################################
ALPHAS = set(ascii_lowercase + ascii_lowercase.upper())
NUMS = set(digits)
IDENTIFIER_START = ALPHAS.union(NUMS)
ESCAPE_CHARS = {'n', '0', 'b', 'f', 'r', 't', 'v', '"', "'", '\\'}
OCTAL = {'0', '1', '2', '3', '4', '5', '6', '7'}
HEX = set('0123456789abcdefABCDEF')
from utils import *
IDENTIFIER_PART = IDENTIFIER_PART.union({'.'})


def _is_cancelled(source, n):
    cancelled = False
    k = 0
    while True:
        k += 1
        if source[n - k] != '\\':
            break
        cancelled = not cancelled
    return cancelled


def _ensure_regexp(source, n):  #<- this function has to be improved
    '''returns True if regexp starts at n else returns False
      checks whether it is not a division '''
    markers = '(+~"\'=[%:?!*^|&-,;/\\'
    k = 0
    while True:
        k += 1
        if n - k < 0:
            return True
        char = source[n - k]
        if char in markers:
            return True
        if char != ' ' and char != '\n':
            break
    return False


def parse_num(source, start, charset):
    """Returns a first index>=start of chat not in charset"""
    while start < len(source) and source[start] in charset:
        start += 1
    return start


def parse_exponent(source, start):
    """returns end of exponential, raises SyntaxError if failed"""
    if not source[start] in {'e', 'E'}:
        if source[start] in IDENTIFIER_PART:
            raise SyntaxError('Invalid number literal!')
        return start
    start += 1
    if source[start] in {'-', '+'}:
        start += 1
    FOUND = False
    # we need at least one dig after exponent
    while source[start] in NUMS:
        FOUND = True
        start += 1
    if not FOUND or source[start] in IDENTIFIER_PART:
        raise SyntaxError('Invalid number literal!')
    return start


def remove_constants(source):
    '''Replaces Strings and Regexp literals in the source code with
       identifiers and *removes comments*. Identifier is of the format:

       PyJsStringConst(String const number)_ - for Strings
       PyJsRegExpConst(RegExp const number)_ - for RegExps

       Returns dict which relates identifier and replaced constant.

       Removes single line and multiline comments from JavaScript source code
       Pseudo comments (inside strings) will not be removed.

       For example this line:
       var x = "/*PSEUDO COMMENT*/ TEXT //ANOTHER PSEUDO COMMENT"
       will be unaltered'''
    source = ' ' + source + '\n'
    comments = []
    inside_comment, single_comment = False, False
    inside_single, inside_double = False, False
    inside_regexp = False
    regexp_class_count = 0
    n = 0
    while n < len(source):
        char = source[n]
        if char == '"' and not (inside_comment or inside_single
                                or inside_regexp):
            if not _is_cancelled(source, n):
                if inside_double:
                    inside_double[1] = n + 1
                    comments.append(inside_double)
                    inside_double = False
                else:
                    inside_double = [n, None, 0]
        elif char == "'" and not (inside_comment or inside_double
                                  or inside_regexp):
            if not _is_cancelled(source, n):
                if inside_single:
                    inside_single[1] = n + 1
                    comments.append(inside_single)
                    inside_single = False
                else:
                    inside_single = [n, None, 0]
        elif (inside_single or inside_double):
            if char in LINE_TERMINATOR:
                if _is_cancelled(source, n):
                    if char == CR and source[n + 1] == LF:
                        n += 1
                    n += 1
                    continue
                else:
                    raise SyntaxError(
                        'Invalid string literal. Line terminators must be escaped!'
                    )
        else:
            if inside_comment:
                if single_comment:
                    if char in LINE_TERMINATOR:
                        inside_comment[1] = n
                        comments.append(inside_comment)
                        inside_comment = False
                        single_comment = False
                else:  # Multiline
                    if char == '/' and source[n - 1] == '*':
                        inside_comment[1] = n + 1
                        comments.append(inside_comment)
                        inside_comment = False
            elif inside_regexp:
                if not quiting_regexp:
                    if char in LINE_TERMINATOR:
                        raise SyntaxError(
                            'Invalid regexp literal. Line terminators cant appear!'
                        )
                    if _is_cancelled(source, n):
                        n += 1
                        continue
                    if char == '[':
                        regexp_class_count += 1
                    elif char == ']':
                        regexp_class_count = max(regexp_class_count - 1, 0)
                    elif char == '/' and not regexp_class_count:
                        quiting_regexp = True
                else:
                    if char not in IDENTIFIER_START:
                        inside_regexp[1] = n
                        comments.append(inside_regexp)
                        inside_regexp = False
            elif char == '/' and source[n - 1] == '/':
                single_comment = True
                inside_comment = [n - 1, None, 1]
            elif char == '*' and source[n - 1] == '/':
                inside_comment = [n - 1, None, 1]
            elif char == '/' and source[n + 1] not in ('/', '*'):
                if not _ensure_regexp(source, n):  #<- improve this one
                    n += 1
                    continue  #Probably just a division
                quiting_regexp = False
                inside_regexp = [n, None, 2]
            elif not (inside_comment or inside_regexp):
                if (char in NUMS and
                        source[n - 1] not in IDENTIFIER_PART) or char == '.':
                    if char == '.':
                        k = parse_num(source, n + 1, NUMS)
                        if k == n + 1:  # just a stupid dot...
                            n += 1
                            continue
                        k = parse_exponent(source, k)
                    elif char == '0' and source[n + 1] in {
                            'x', 'X'
                    }:  #Hex number probably
                        k = parse_num(source, n + 2, HEX)
                        if k == n + 2 or source[k] in IDENTIFIER_PART:
                            raise SyntaxError('Invalid hex literal!')
                    else:  #int or exp or flot or exp flot
                        k = parse_num(source, n + 1, NUMS)
                        if source[k] == '.':
                            k = parse_num(source, k + 1, NUMS)
                        k = parse_exponent(source, k)
                    comments.append((n, k, 3))
                    n = k
                    continue
        n += 1
    res = ''
    start = 0
    count = 0
    constants = {}
    for end, next_start, typ in comments:
        res += source[start:end]
        start = next_start
        if typ == 0:  # String
            name = StringName
        elif typ == 1:  # comment
            continue
        elif typ == 2:  # regexp
            name = RegExpName
        elif typ == 3:  # number
            name = NumberName
        else:
            raise RuntimeError()
        res += ' ' + name % count + ' '
        constants[name % count] = source[end:next_start]
        count += 1
    res += source[start:]
    # remove this stupid white space
    for e in WHITE:
        res = res.replace(e, ' ')
    res = res.replace(CR + LF, '\n')
    for e in LINE_TERMINATOR:
        res = res.replace(e, '\n')
    return res.strip(), constants


def recover_constants(py_source,
                      replacements):  #now has n^2 complexity. improve to n
    '''Converts identifiers representing Js constants to the PyJs constants
    PyJsNumberConst_1_ which has the true value of 5 will be converted to PyJsNumber(5)'''
    for identifier, value in replacements.iteritems():
        if identifier.startswith('PyJsConstantRegExp'):
            py_source = py_source.replace(identifier,
                                          'JsRegExp(%s)' % repr(value))
        elif identifier.startswith('PyJsConstantString'):
            py_source = py_source.replace(
                identifier, 'Js(u%s)' % unify_string_literals(value))
        else:
            py_source = py_source.replace(identifier, 'Js(%s)' % value)
    return py_source


def unify_string_literals(js_string):
    """this function parses the string just like javascript
       for example literal '\d' in JavaScript would be interpreted
       as 'd' - backslash would be ignored and in Pyhon this
       would be interpreted as '\\d' This function fixes this problem."""
    n = 0
    res = ''
    limit = len(js_string)
    while n < limit:
        char = js_string[n]
        if char == '\\':
            new, n = do_escape(js_string, n)
            res += new
        else:
            res += char
            n += 1
    return res


def unify_regexp_literals(js):
    pass


def do_escape(source, n):
    """Its actually quite complicated to cover every case :)
       http://www.javascriptkit.com/jsref/escapesequence.shtml"""
    if not n + 1 < len(source):
        return ''  # not possible here but can be possible in general case.
    if source[n + 1] in LINE_TERMINATOR:
        if source[n + 1] == CR and n + 2 < len(source) and source[n + 2] == LF:
            return source[n:n + 3], n + 3
        return source[n:n + 2], n + 2
    if source[n + 1] in ESCAPE_CHARS:
        return source[n:n + 2], n + 2
    if source[n + 1] in {'x', 'u'}:
        char, length = ('u', 4) if source[n + 1] == 'u' else ('x', 2)
        n += 2
        end = parse_num(source, n, HEX)
        if end - n < length:
            raise SyntaxError('Invalid escape sequence!')
        #if length==4:
        #    return unichr(int(source[n:n+4], 16)), n+4 # <- this was a very bad way of solving this problem :)
        return source[n - 2:n + length], n + length
    if source[n + 1] in OCTAL:
        n += 1
        end = parse_num(source, n, OCTAL)
        end = min(end, n + 3)  # cant be longer than 3
        # now the max allowed is 377 ( in octal) and 255 in decimal
        max_num = 255
        num = 0
        len_parsed = 0
        for e in source[n:end]:
            cand = 8 * num + int(e)
            if cand > max_num:
                break
            num = cand
            len_parsed += 1
        # we have to return in a different form because python may want to parse more...
        # for example '\777' will be parsed by python as a whole while js will use only \77
        return '\\' + hex(num)[1:], n + len_parsed
    return source[n + 1], n + 2


#####TEST######

if __name__ == '__main__':
    test = ('''
    ''')

    t, d = remove_constants(test)
    print t, d
