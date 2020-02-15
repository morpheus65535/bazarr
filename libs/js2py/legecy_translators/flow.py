"""This module translates JS flow into PY flow.

Translates:
IF ELSE

DO WHILE
WHILE
FOR 123
FOR iter
CONTINUE, BREAK, RETURN, LABEL, THROW, TRY, SWITCH
"""
from __future__ import print_function

from utils import *
from jsparser import *
from nodevisitor import exp_translator
import random

TO_REGISTER = []
CONTINUE_LABEL = 'JS_CONTINUE_LABEL_%s'
BREAK_LABEL = 'JS_BREAK_LABEL_%s'

PREPARE = '''HOLDER = var.own.get(NAME)\nvar.force_own_put(NAME, PyExceptionToJs(PyJsTempException))\n'''
RESTORE = '''if HOLDER is not None:\n    var.own[NAME] = HOLDER\nelse:\n    del var.own[NAME]\ndel HOLDER\n'''
TRY_CATCH = '''%stry:\nBLOCKfinally:\n%s''' % (PREPARE, indent(RESTORE))


def get_continue_label(label):
    return CONTINUE_LABEL % label.encode('hex')


def get_break_label(label):
    return BREAK_LABEL % label.encode('hex')


def pass_until(source, start, tokens=(';', )):
    while start < len(source) and source[start] not in tokens:
        start += 1
    return start + 1


def do_bracket_exp(source, start, throw=True):
    bra, cand = pass_bracket(source, start, '()')
    if throw and not bra:
        raise SyntaxError('Missing bracket expression')
    bra = exp_translator(bra[1:-1])
    if throw and not bra:
        raise SyntaxError('Empty bracket condition')
    return bra, cand if bra else start


def do_if(source, start):
    start += 2  # pass this if
    bra, start = do_bracket_exp(source, start, throw=True)
    statement, start = do_statement(source, start)
    if statement is None:
        raise SyntaxError('Invalid if statement')
    translated = 'if %s:\n' % bra + indent(statement)

    elseif = except_keyword(source, start, 'else')
    is_elseif = False
    if elseif:
        start = elseif
        if except_keyword(source, start, 'if'):
            is_elseif = True
        elseif, start = do_statement(source, start)
        if elseif is None:
            raise SyntaxError('Invalid if statement)')
        if is_elseif:
            translated += 'el' + elseif
        else:
            translated += 'else:\n' + indent(elseif)
    return translated, start


def do_statement(source, start):
    """returns none if not found other functions that begin with 'do_' raise
    also this do_ type function passes white space"""
    start = pass_white(source, start)
    # start is the fist position after initial start that is not a white space or \n
    if not start < len(source):  #if finished parsing return None
        return None, start
    if any(startswith_keyword(source[start:], e) for e in {'case', 'default'}):
        return None, start
    rest = source[start:]
    for key, meth in KEYWORD_METHODS.iteritems(
    ):  # check for statements that are uniquely defined by their keywords
        if rest.startswith(key):
            # has to startwith this keyword and the next letter after keyword must be either EOF or not in IDENTIFIER_PART
            if len(key) == len(rest) or rest[len(key)] not in IDENTIFIER_PART:
                return meth(source, start)
    if rest[0] == '{':  #Block
        return do_block(source, start)
    # Now only label and expression left
    cand = parse_identifier(source, start, False)
    if cand is not None:  # it can mean that its a label
        label, cand_start = cand
        cand_start = pass_white(source, cand_start)
        if source[cand_start] == ':':
            return do_label(source, start)
    return do_expression(source, start)


def do_while(source, start):
    start += 5  # pass while
    bra, start = do_bracket_exp(source, start, throw=True)
    statement, start = do_statement(source, start)
    if statement is None:
        raise SyntaxError('Missing statement to execute in while loop!')
    return 'while %s:\n' % bra + indent(statement), start


def do_dowhile(source, start):
    start += 2  # pass do
    statement, start = do_statement(source, start)
    if statement is None:
        raise SyntaxError('Missing statement to execute in do while loop!')
    start = except_keyword(source, start, 'while')
    if not start:
        raise SyntaxError('Missing while keyword in do-while loop')
    bra, start = do_bracket_exp(source, start, throw=True)
    statement += 'if not %s:\n' % bra + indent('break\n')
    return 'while 1:\n' + indent(statement), start


def do_block(source, start):
    bra, start = pass_bracket(source, start, '{}')
    #print source[start:], bra
    #return bra +'\n', start
    if bra is None:
        raise SyntaxError('Missing block ( {code} )')
    code = ''
    bra = bra[1:-1] + ';'
    bra_pos = 0
    while bra_pos < len(bra):
        st, bra_pos = do_statement(bra, bra_pos)
        if st is None:
            break
        code += st
    bra_pos = pass_white(bra, bra_pos)
    if bra_pos < len(bra):
        raise SyntaxError('Block has more code that could not be parsed:\n' +
                          bra[bra_pos:])
    return code, start


def do_empty(source, start):
    return 'pass\n', start + 1


def do_expression(source, start):
    start = pass_white(source, start)
    end = pass_until(source, start, tokens=(';', ))
    if end == start + 1:  #empty statement
        return 'pass\n', end
    # AUTOMATIC SEMICOLON INSERTION FOLLOWS
    # Without ASI this function would end with: return exp_translator(source[start:end].rstrip(';'))+'\n', end
    # ASI makes things a bit more complicated:
    # we will try to parse as much as possible, inserting ; in place of last new line in case of error
    rev = False
    rpos = 0
    while True:
        try:
            code = source[start:end].rstrip(';')
            cand = exp_translator(code) + '\n', end
            just_to_test = compile(cand[0], '', 'exec')
            return cand
        except Exception as e:
            if not rev:
                rev = source[start:end][::-1]
        lpos = rpos
        while True:
            rpos = pass_until(rev, rpos, LINE_TERMINATOR)
            if rpos >= len(rev):
                raise
            if filter(lambda x: x not in SPACE, rev[lpos:rpos]):
                break
        end = start + len(rev) - rpos + 1


def do_var(source, start):
    #todo auto ; insertion
    start += 3  #pass var
    end = pass_until(source, start, tokens=(';', ))
    defs = argsplit(
        source[start:end - 1]
    )  # defs is the list of defined vars with optional initializer
    code = ''
    for de in defs:
        var, var_end = parse_identifier(de, 0, True)
        TO_REGISTER.append(var)
        var_end = pass_white(de, var_end)
        if var_end < len(
                de
        ):  # we have something more to parse... It has to start with =
            if de[var_end] != '=':
                raise SyntaxError(
                    'Unexpected initializer in var statement. Expected "=", got "%s"'
                    % de[var_end])
            code += exp_translator(de) + '\n'
    if not code.strip():
        code = 'pass\n'
    return code, end


def do_label(source, start):
    label, end = parse_identifier(source, start)
    end = pass_white(source, end)
    #now source[end] must be :
    assert source[end] == ':'
    end += 1
    inside, end = do_statement(source, end)
    if inside is None:
        raise SyntaxError('Missing statement after label')
    defs = ''
    if inside.startswith('while ') or inside.startswith(
            'for ') or inside.startswith('#for'):
        # we have to add contine label as well...
        # 3 or 1 since #for loop type has more lines before real for.
        sep = 1 if not inside.startswith('#for') else 3
        cont_label = get_continue_label(label)
        temp = inside.split('\n')
        injected = 'try:\n' + '\n'.join(temp[sep:])
        injected += 'except %s:\n    pass\n' % cont_label
        inside = '\n'.join(temp[:sep]) + '\n' + indent(injected)
        defs += 'class %s(Exception): pass\n' % cont_label
    break_label = get_break_label(label)
    inside = 'try:\n%sexcept %s:\n    pass\n' % (indent(inside), break_label)
    defs += 'class %s(Exception): pass\n' % break_label
    return defs + inside, end


def do_for(source, start):
    start += 3  # pass for
    entered = start
    bra, start = pass_bracket(source, start, '()')
    inside, start = do_statement(source, start)
    if inside is None:
        raise SyntaxError('Missing statement after for')
    bra = bra[1:-1]
    if ';' in bra:
        init = argsplit(bra, ';')
        if len(init) != 3:
            raise SyntaxError('Invalid for statement')
        args = []
        for i, item in enumerate(init):
            end = pass_white(item, 0)
            if end == len(item):
                args.append('' if i != 1 else '1')
                continue
            if not i and except_keyword(item, end, 'var') is not None:
                # var statement
                args.append(do_var(item, end)[0])
                continue
            args.append(do_expression(item, end)[0])
        return '#for JS loop\n%swhile %s:\n%s%s\n' % (
            args[0], args[1].strip(), indent(inside), indent(args[2])), start
    # iteration
    end = pass_white(bra, 0)
    register = False
    if bra[end:].startswith('var '):
        end += 3
        end = pass_white(bra, end)
        register = True
    name, end = parse_identifier(bra, end)
    if register:
        TO_REGISTER.append(name)
    end = pass_white(bra, end)
    if bra[end:end + 2] != 'in' or bra[end + 2] in IDENTIFIER_PART:
        #print source[entered-10:entered+50]
        raise SyntaxError('Invalid "for x in y" statement')
    end += 2  # pass in
    exp = exp_translator(bra[end:])
    res = 'for temp in %s:\n' % exp
    res += indent('var.put(%s, temp)\n' % name.__repr__()) + indent(inside)
    return res, start


# todo - IMPORTANT
def do_continue(source, start, name='continue'):
    start += len(name)  #pass continue
    start = pass_white(source, start)
    if start < len(source) and source[start] == ';':
        return '%s\n' % name, start + 1
    # labeled statement or error
    label, start = parse_identifier(source, start)
    start = pass_white(source, start)
    if start < len(source) and source[start] != ';':
        raise SyntaxError('Missing ; after label name in %s statement' % name)
    return 'raise %s("%s")\n' % (get_continue_label(label)
                                 if name == 'continue' else
                                 get_break_label(label), name), start + 1


def do_break(source, start):
    return do_continue(source, start, 'break')


def do_return(source, start):
    start += 6  # pass return
    end = source.find(';', start) + 1
    if end == -1:
        end = len(source)
    trans = exp_translator(source[start:end].rstrip(';'))
    return 'return %s\n' % (trans if trans else "var.get('undefined')"), end


# todo later?- Also important
def do_throw(source, start):
    start += 5  # pass throw
    end = source.find(';', start) + 1
    if not end:
        end = len(source)
    trans = exp_translator(source[start:end].rstrip(';'))
    if not trans:
        raise SyntaxError('Invalid throw statement: nothing to throw')
    res = 'PyJsTempException = JsToPyException(%s)\nraise PyJsTempException\n' % trans
    return res, end


def do_try(source, start):
    start += 3  # pass try
    block, start = do_block(source, start)
    result = 'try:\n%s' % indent(block)
    catch = except_keyword(source, start, 'catch')
    if catch:
        bra, catch = pass_bracket(source, catch, '()')
        bra = bra[1:-1]
        identifier, bra_end = parse_identifier(bra, 0)
        holder = 'PyJsHolder_%s_%d' % (identifier.encode('hex'),
                                       random.randrange(1e8))
        identifier = identifier.__repr__()
        bra_end = pass_white(bra, bra_end)
        if bra_end < len(bra):
            raise SyntaxError('Invalid content of catch statement')
        result += 'except PyJsException as PyJsTempException:\n'
        block, catch = do_block(source, catch)
        # fill in except ( catch ) block and remember to recover holder variable to its previous state
        result += indent(
            TRY_CATCH.replace('HOLDER', holder).replace('NAME',
                                                        identifier).replace(
                                                            'BLOCK',
                                                            indent(block)))
    start = max(catch, start)
    final = except_keyword(source, start, 'finally')
    if not (final or catch):
        raise SyntaxError(
            'Try statement has to be followed by catch or finally')
    if not final:
        return result, start
    # translate finally statement
    block, start = do_block(source, final)
    return result + 'finally:\n%s' % indent(block), start


def do_debugger(source, start):
    start += 8  # pass debugger
    end = pass_white(source, start)
    if end < len(source) and source[end] == ';':
        end += 1
    return 'pass\n', end  #ignore errors...


# todo automatic ; insertion. fuck this crappy feature

# Least important


def do_switch(source, start):
    start += 6  # pass switch
    code = 'while 1:\n' + indent('SWITCHED = False\nCONDITION = (%s)\n')
    # parse value of check
    val, start = pass_bracket(source, start, '()')
    if val is None:
        raise SyntaxError('Missing () after switch statement')
    if not val.strip():
        raise SyntaxError('Missing content inside () after switch statement')
    code = code % exp_translator(val)
    bra, start = pass_bracket(source, start, '{}')
    if bra is None:
        raise SyntaxError('Missing block {} after switch statement')
    bra_pos = 0
    bra = bra[1:-1] + ';'
    while True:
        case = except_keyword(bra, bra_pos, 'case')
        default = except_keyword(bra, bra_pos, 'default')
        assert not (case and default)
        if case or default:  # this ?: expression makes things much harder....
            case_code = None
            if case:
                case_code = 'if SWITCHED or PyJsStrictEq(CONDITION, %s):\n'
                # we are looking for a first : with count 1. ? gives -1 and : gives +1.
                count = 0
                for pos, e in enumerate(bra[case:], case):
                    if e == '?':
                        count -= 1
                    elif e == ':':
                        count += 1
                        if count == 1:
                            break
                else:
                    raise SyntaxError(
                        'Missing : token after case in switch statement')
                case_condition = exp_translator(
                    bra[case:pos])  # switch {case CONDITION: statements}
                case_code = case_code % case_condition
                case = pos + 1
            if default:
                case = except_token(bra, default, ':')
                case_code = 'if True:\n'
            # now parse case statements (things after ':' )
            cand, case = do_statement(bra, case)
            while cand:
                case_code += indent(cand)
                cand, case = do_statement(bra, case)
            case_code += indent('SWITCHED = True\n')
            code += indent(case_code)
            bra_pos = case
        else:
            break
    # prevent infinite loop :)
    code += indent('break\n')
    return code, start


def do_pyimport(source, start):
    start += 8
    lib, start = parse_identifier(source, start)
    jlib = 'PyImport_%s' % lib
    code = 'import %s as %s\n' % (lib, jlib)
    #check whether valid lib name...
    try:
        compile(code, '', 'exec')
    except:
        raise SyntaxError(
            'Invalid Python module name (%s) in pyimport statement' % lib)
    # var.pyimport will handle module conversion to PyJs object
    code += 'var.pyimport(%s, %s)\n' % (repr(lib), jlib)
    return code, start


def do_with(source, start):
    raise NotImplementedError('With statement is not implemented yet :(')


KEYWORD_METHODS = {
    'do': do_dowhile,
    'while': do_while,
    'if': do_if,
    'throw': do_throw,
    'return': do_return,
    'continue': do_continue,
    'break': do_break,
    'try': do_try,
    'for': do_for,
    'switch': do_switch,
    'var': do_var,
    'debugger': do_debugger,  # this one does not do anything
    'with': do_with,
    'pyimport': do_pyimport
}

#Also not specific statements (harder to detect)
# Block {}
# Expression or Empty Statement
# Label
#
# Its easy to recognize block but harder to distinguish between label and expression statement


def translate_flow(source):
    """Source cant have arrays, object, constant or function literals.
       Returns PySource and variables to register"""
    global TO_REGISTER
    TO_REGISTER = []
    return do_block('{%s}' % source, 0)[0], TO_REGISTER


if __name__ == '__main__':
    #print do_dowhile('do {} while(k+f)', 0)[0]
    #print 'e: "%s"'%do_expression('++(c?g:h);   mj', 0)[0]
    print(translate_flow('a; yimport test')[0])
