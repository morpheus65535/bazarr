"""
exp_translate routine:
It takes a single line of JS code and returns a SINGLE line of Python code.
Note var is not present here because it was removed in previous stages. Also remove this useless void keyword
If case of parsing errors it must return a pos of error.
1. Convert all assignment operations to put operations, this may be hard :( DONE, wasn't that bad
2. Convert all gets and calls to get and callprop.
3. Convert unary operators like typeof, new, !, delete, ++, --
   Delete can be handled by replacing last get method with delete.
4. Convert remaining operators that are not handled by python:
    &&, || <= these should be easy simply replace && by and and || by or
    === and !==
    comma operator , in, instanceof and finally :?


NOTES:
Strings and other literals are not present so each = means assignment
"""
from __future__ import print_function

from utils import *
from jsparser import *


def exps_translator(js):
    #Check  () {} and [] nums
    ass = assignment_translator(js)


# Step 1
def assignment_translator(js):
    sep = js.split(',')
    res = sep[:]
    for i, e in enumerate(sep):
        if '=' not in e:  # no need to convert
            continue
        res[i] = bass_translator(e)
    return ','.join(res)


def bass_translator(s):
    # I hope that I will not have to fix any bugs here because it will be terrible
    if '(' in s or '[' in s:
        converted = ''
        for e in bracket_split(s, ['()', '[]'], strip=False):
            if e[0] == '(':
                converted += '(' + bass_translator(e[1:-1]) + ')'
            elif e[0] == '[':
                converted += '[' + bass_translator(e[1:-1]) + ']'
            else:
                converted += e
        s = converted
    if '=' not in s:
        return s
    ass = reversed(s.split('='))
    last = ass.next()
    res = last
    for e in ass:
        op = ''
        if e[-1] in OP_METHODS:  #increment assign like +=
            op = ', "' + e[-1] + '"'
            e = e[:-1]
        cand = e.strip(
            '() ')  # (a) = 40 is valid so we need to transform  '(a) ' to 'a'
        if not is_property_accessor(cand):  # it is not a property assignment
            if not is_lval(cand) or is_internal(cand):
                raise SyntaxError('Invalid left-hand side in assignment')
            res = 'var.put(%s, %s%s)' % (cand.__repr__(), res, op)
        elif cand[-1] == ']':  # property assignment via []
            c = list(bracket_split(cand, ['[]'], strip=False))
            meth, prop = ''.join(c[:-1]).strip(), c[-1][1:-1].strip(
            )  #this does not have to be a string so dont remove
            #() because it can be a call
            res = '%s.put(%s, %s%s)' % (meth, prop, res, op)
        else:  # Prop set via '.'
            c = cand.rfind('.')
            meth, prop = cand[:c].strip(), cand[c + 1:].strip('() ')
            if not is_lval(prop):
                raise SyntaxError('Invalid left-hand side in assignment')
            res = '%s.put(%s, %s%s)' % (meth, prop.__repr__(), res, op)
    return res


if __name__ == '__main__':
    print(bass_translator('3.ddsd = 40'))
