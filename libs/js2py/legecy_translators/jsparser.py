"""
The process of translating JS will go like that:        # TOP = 'imports and scope set'

1. Remove all the comments
2. Replace number, string and regexp literals with markers
4. Remove global Functions and move their translation to the TOP. Also add register code there.
5. Replace inline functions with lvals
6. Remove List and Object literals and replace them with lvals
7. Find and remove var declarations, generate python register code that would go on TOP.

Here we should be left with global code only where 1 line of js code = 1 line of python code.
Routine translating this code should be called glob_translate:
1. Search for outer structures and translate them using glob and inside using exps_translate


exps_translate routine:
1. Remove outer {}
2. Split lines at ;
3. Convert line by line using exp_translate
4. In case of error in 3 try to insert ; according to ECMA rules and repeat 3.

exp_translate routine:
It takes a single line of JS code and returns a SINGLE line of Python code.
Note var is not present here because it was removed in previous stages.
If case of parsing errors it must return a pos of error.
1. Convert all assignment operations to put operations, this may be hard :(
2. Convert all gets and calls to get and callprop.
3. Convert unary operators like typeof, new, !, delete.
   Delete can be handled by replacing last get method with delete.
4. Convert remaining operators that are not handled by python eg: === and ,





lval format PyJsLvalNR
marker PyJs(TYPE_NAME)(NR)

TODO
1. Number literal replacement
2. Array literal replacement
3. Object literal replacement
5. Function replacement
4. Literal replacement translators


"""

from utils import *

OP_METHODS = {
    '*': '__mul__',
    '/': '__div__',
    '%': '__mod__',
    '+': '__add__',
    '-': '__sub__',
    '<<': '__lshift__',
    '>>': '__rshift__',
    '&': '__and__',
    '^': '__xor__',
    '|': '__or__'
}


def dbg(source):
    try:
        with open('C:\Users\Piotrek\Desktop\dbg.py', 'w') as f:
            f.write(source)
    except:
        pass


def indent(lines, ind=4):
    return ind * ' ' + lines.replace('\n', '\n' + ind * ' ').rstrip(' ')


def inject_before_lval(source, lval, code):
    if source.count(lval) > 1:
        dbg(source)
        print
        print lval
        raise RuntimeError('To many lvals (%s)' % lval)
    elif not source.count(lval):
        dbg(source)
        print
        print lval
        assert lval not in source
        raise RuntimeError('No lval found "%s"' % lval)
    end = source.index(lval)
    inj = source.rfind('\n', 0, end)
    ind = inj
    while source[ind + 1] == ' ':
        ind += 1
    ind -= inj
    return source[:inj + 1] + indent(code, ind) + source[inj + 1:]


def bracket_split(source, brackets=('()', '{}', '[]'), strip=False):
    """DOES NOT RETURN EMPTY STRINGS (can only return empty bracket content if strip=True)"""
    starts = [e[0] for e in brackets]
    in_bracket = 0
    n = 0
    last = 0
    while n < len(source):
        e = source[n]
        if not in_bracket and e in starts:
            in_bracket = 1
            start = n
            b_start, b_end = brackets[starts.index(e)]
        elif in_bracket:
            if e == b_start:
                in_bracket += 1
            elif e == b_end:
                in_bracket -= 1
                if not in_bracket:
                    if source[last:start]:
                        yield source[last:start]
                    last = n + 1
                    yield source[start + strip:n + 1 - strip]
        n += 1
    if source[last:]:
        yield source[last:]


def pass_bracket(source, start, bracket='()'):
    """Returns content of brackets with brackets and first pos after brackets
     if source[start] is followed by some optional white space and brackets.
     Otherwise None"""
    e = bracket_split(source[start:], [bracket], False)
    try:
        cand = e.next()
    except StopIteration:
        return None, None
    if not cand.strip():  #white space...
        try:
            res = e.next()
            return res, start + len(cand) + len(res)
        except StopIteration:
            return None, None
    elif cand[-1] == bracket[1]:
        return cand, start + len(cand)
    else:
        return None, None


def startswith_keyword(start, keyword):
    start = start.lstrip()
    if start.startswith(keyword):
        if len(keyword) < len(start):
            if start[len(keyword)] in IDENTIFIER_PART:
                return False
        return True
    return False


def endswith_keyword(ending, keyword):
    ending = ending.rstrip()
    if ending.endswith(keyword):
        if len(keyword) < len(ending):
            if ending[len(ending) - len(keyword) - 1] in IDENTIFIER_PART:
                return False
        return True
    return False


def pass_white(source, start):
    n = start
    while n < len(source):
        if source[n] in SPACE:
            n += 1
        else:
            break
    return n


def except_token(source, start, token, throw=True):
    """Token can be only a single char. Returns position after token if found. Otherwise raises syntax error if throw
    otherwise returns None"""
    start = pass_white(source, start)
    if start < len(source) and source[start] == token:
        return start + 1
    if throw:
        raise SyntaxError('Missing token. Expected %s' % token)
    return None


def except_keyword(source, start, keyword):
    """ Returns position after keyword if found else None
        Note: skips white space"""
    start = pass_white(source, start)
    kl = len(keyword)  #keyword len
    if kl + start > len(source):
        return None
    if source[start:start + kl] != keyword:
        return None
    if kl + start < len(source) and source[start + kl] in IDENTIFIER_PART:
        return None
    return start + kl


def parse_identifier(source, start, throw=True):
    """passes white space from start and returns first identifier,
       if identifier invalid and throw raises SyntaxError otherwise returns None"""
    start = pass_white(source, start)
    end = start
    if not end < len(source):
        if throw:
            raise SyntaxError('Missing identifier!')
        return None
    if source[end] not in IDENTIFIER_START:
        if throw:
            raise SyntaxError('Invalid identifier start: "%s"' % source[end])
        return None
    end += 1
    while end < len(source) and source[end] in IDENTIFIER_PART:
        end += 1
    if not is_valid_lval(source[start:end]):
        if throw:
            raise SyntaxError(
                'Invalid identifier name: "%s"' % source[start:end])
        return None
    return source[start:end], end


def argsplit(args, sep=','):
    """used to split JS args (it is not that simple as it seems because
       sep can be inside brackets).

       pass args *without* brackets!

       Used also to parse array and object elements, and more"""
    parsed_len = 0
    last = 0
    splits = []
    for e in bracket_split(args, brackets=['()', '[]', '{}']):
        if e[0] not in {'(', '[', '{'}:
            for i, char in enumerate(e):
                if char == sep:
                    splits.append(args[last:parsed_len + i])
                    last = parsed_len + i + 1
        parsed_len += len(e)
    splits.append(args[last:])
    return splits


def split_add_ops(text):
    """Specialized function splitting text at add/sub operators.
    Operands are *not* translated. Example result ['op1', '+', 'op2', '-', 'op3']"""
    n = 0
    text = text.replace('++', '##').replace(
        '--', '@@')  #text does not normally contain any of these
    spotted = False  # set to true if noticed anything other than +- or white space
    last = 0
    while n < len(text):
        e = text[n]
        if e == '+' or e == '-':
            if spotted:
                yield text[last:n].replace('##', '++').replace('@@', '--')
                yield e
                last = n + 1
                spotted = False
        elif e == '/' or e == '*' or e == '%':
            spotted = False
        elif e != ' ':
            spotted = True
        n += 1
    yield text[last:n].replace('##', '++').replace('@@', '--')


def split_at_any(text,
                 lis,
                 translate=False,
                 not_before=[],
                 not_after=[],
                 validitate=None):
    """ doc """
    lis.sort(key=lambda x: len(x), reverse=True)
    last = 0
    n = 0
    text_len = len(text)
    while n < text_len:
        if any(text[:n].endswith(e)
               for e in not_before):  #Cant end with end before
            n += 1
            continue
        for e in lis:
            s = len(e)
            if s + n > text_len:
                continue
            if validitate and not validitate(e, text[:n], text[n + s:]):
                continue
            if any(text[n + s:].startswith(e)
                   for e in not_after):  #Cant end with end before
                n += 1
                break
            if e == text[n:n + s]:
                yield text[last:n] if not translate else translate(
                    text[last:n])
                yield e
                n += s
                last = n
                break
        else:
            n += 1
    yield text[last:n] if not translate else translate(text[last:n])


def split_at_single(text, sep, not_before=[], not_after=[]):
    """Works like text.split(sep) but separated fragments
    cant end with not_before or start with not_after"""
    n = 0
    lt, s = len(text), len(sep)
    last = 0
    while n < lt:
        if not s + n > lt:
            if sep == text[n:n + s]:
                if any(text[last:n].endswith(e) for e in not_before):
                    pass
                elif any(text[n + s:].startswith(e) for e in not_after):
                    pass
                else:
                    yield text[last:n]
                    last = n + s
                    n += s - 1
        n += 1
    yield text[last:]
