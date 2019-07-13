"""This module removes JS functions from source code"""
from jsparser import *
from utils import *

INLINE_NAME = 'PyJsLvalInline%d_'
INLINE_COUNT = 0
PRE_EXP_STARTS = {
    'return', 'new', 'void', 'throw', 'typeof', 'in', 'instanceof'
}
PRE_ALLOWED = IDENTIFIER_PART.union({';', '{', '}', ']', ')', ':'})
INCREMENTS = {'++', '--'}


def reset_inline_count():
    global INLINE_COUNT
    INLINE_COUNT = 0


def remove_functions(source, all_inline=False):
    """removes functions and returns new source, and 2 dicts.
        first dict with removed hoisted(global) functions and second with replaced inline functions"""
    global INLINE_COUNT
    inline = {}
    hoisted = {}
    n = 0
    limit = len(source) - 9  # 8 is length of 'function'
    res = ''
    last = 0
    while n < limit:
        if n and source[n - 1] in IDENTIFIER_PART:
            n += 1
            continue
        if source[n:n + 8] == 'function' and source[n +
                                                    8] not in IDENTIFIER_PART:
            if source[:n].rstrip().endswith(
                    '.'):  # allow function as a property name :)
                n += 1
                continue
            if source[n + 8:].lstrip().startswith(
                    ':'):  # allow functions inside objects...
                n += 1
                continue
            entered = n
            res += source[last:n]
            name = ''
            n = pass_white(source, n + 8)
            if source[n] in IDENTIFIER_START:  # hoisted function
                name, n = parse_identifier(source, n)
            args, n = pass_bracket(source, n, '()')
            if not args:
                raise SyntaxError('Function misses bracket with argnames ()')
            args = args.strip('() \n')
            args = tuple(parse_identifier(e, 0)[0]
                         for e in argsplit(args)) if args else ()
            if len(args) - len(set(args)):
                # I know its legal in JS but python does not allow duplicate argnames
                # I will not work around it
                raise SyntaxError(
                    'Function has duplicate argument names. Its not legal in this implementation. Sorry.'
                )
            block, n = pass_bracket(source, n, '{}')
            if not block:
                raise SyntaxError(
                    'Function does not have any code block to execute')
            mixed = False  # named function expression flag
            if name and not all_inline:
                # Here I will distinguish between named function expression (mixed) and a function statement
                before = source[:entered].rstrip()
                if any(endswith_keyword(before, e) for e in PRE_EXP_STARTS):
                    #print 'Ended ith keyword'
                    mixed = True
                elif before and before[-1] not in PRE_ALLOWED and not before[
                        -2:] in INCREMENTS:
                    #print 'Ended with'+repr(before[-1]), before[-1]=='}'
                    mixed = True
                else:
                    #print 'FUNCTION STATEMENT'
                    #its a function statement.
                    # todo remove fucking label if present!
                    hoisted[name] = block, args
            if not name or mixed or all_inline:  # its a function expression (can be both named and not named)
                #print 'FUNCTION EXPRESSION'
                INLINE_COUNT += 1
                iname = INLINE_NAME % INLINE_COUNT  # inline name
                res += ' ' + iname
                inline['%s@%s' % (
                    iname, name
                )] = block, args  #here added real name at the end because it has to be added to the func scope
            last = n
        else:
            n += 1
    res += source[last:]
    return res, hoisted, inline


if __name__ == '__main__':
    print remove_functions(
        '5+5 function n  (functiona ,functionaj) {dsd  s, dsdd}')
