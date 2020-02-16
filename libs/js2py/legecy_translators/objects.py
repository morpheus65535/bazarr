""" This module removes all objects/arrays from JS source code and replace them with LVALS.
Also it has  s function translating removed object/array to python code.
Use this module just after removing constants. Later move on to removing functions"""
from __future__ import print_function

OBJECT_LVAL = 'PyJsLvalObject%d_'
ARRAY_LVAL = 'PyJsLvalArray%d_'
from utils import *
from jsparser import *
from nodevisitor import exp_translator
import functions
from flow import KEYWORD_METHODS


def FUNC_TRANSLATOR(*a):  #  stupid import system in python
    raise RuntimeError('Remember to set func translator. Thank you.')


def set_func_translator(ftrans):
    # stupid stupid Python or Peter
    global FUNC_TRANSLATOR
    FUNC_TRANSLATOR = ftrans


def is_empty_object(n, last):
    """n may be the inside of block or object"""
    if n.strip():
        return False
    # seems to be but can be empty code
    last = last.strip()
    markers = {
        ')',
        ';',
    }
    if not last or last[-1] in markers:
        return False
    return True


# todo refine this function
def is_object(n, last):
    """n may be the inside of block or object.
       last is the code before object"""
    if is_empty_object(n, last):
        return True
    if not n.strip():
        return False
    #Object contains lines of code so it cant be an object
    if len(argsplit(n, ';')) > 1:
        return False
    cands = argsplit(n, ',')
    if not cands[-1].strip():
        return True  # {xxxx,} empty after last , it must be an object
    for cand in cands:
        cand = cand.strip()
        # separate each candidate element at : in dict and check whether they are correct...
        kv = argsplit(cand, ':')
        if len(
                kv
        ) > 2:  # set the len of kv to 2 because of this stupid : expression
            kv = kv[0], ':'.join(kv[1:])

        if len(kv) == 2:
            # key value pair, check whether not label or ?:
            k, v = kv
            if not is_lval(k.strip()):
                return False
            v = v.strip()
            if v.startswith('function'):
                continue
            #will fail on label... {xxx: while {}}
            if v[0] == '{':  # value cant be a code block
                return False
            for e in KEYWORD_METHODS:
                # if v starts with any statement then return false
                if v.startswith(e) and len(e) < len(v) and v[len(
                        e)] not in IDENTIFIER_PART:
                    return False
        elif not (cand.startswith('set ') or cand.startswith('get ')):
            return False
    return True


def is_array(last):
    #it can be prop getter
    last = last.strip()
    if any(
            endswith_keyword(last, e) for e in
        {'return', 'new', 'void', 'throw', 'typeof', 'in', 'instanceof'}):
        return True
    markers = {')', ']'}
    return not last or not (last[-1] in markers or last[-1] in IDENTIFIER_PART)


def remove_objects(code, count=1):
    """ This function replaces objects with OBJECTS_LVALS, returns new code, replacement dict and count.
        count arg is the number that should be added to the LVAL of the first replaced object
    """
    replacements = {}  #replacement dict
    br = bracket_split(code, ['{}', '[]'])
    res = ''
    last = ''
    for e in br:
        #test whether e is an object
        if e[0] == '{':
            n, temp_rep, cand_count = remove_objects(e[1:-1], count)
            # if e was not an object then n should not contain any :
            if is_object(n, last):
                #e was an object
                res += ' ' + OBJECT_LVAL % count
                replacements[OBJECT_LVAL % count] = e
                count += 1
            else:
                # e was just a code block but could contain objects inside
                res += '{%s}' % n
                count = cand_count
                replacements.update(temp_rep)
        elif e[0] == '[':
            if is_array(last):
                res += e  # will be translated later
            else:  # prop get
                n, rep, count = remove_objects(e[1:-1], count)
                res += '[%s]' % n
                replacements.update(rep)
        else:  # e does not contain any objects
            res += e
        last = e  #needed to test for this stipid empty object
    return res, replacements, count


def remove_arrays(code, count=1):
    """removes arrays and replaces them with ARRAY_LVALS
       returns new code and replacement dict
       *NOTE* has to be called AFTER remove objects"""
    res = ''
    last = ''
    replacements = {}
    for e in bracket_split(code, ['[]']):
        if e[0] == '[':
            if is_array(last):
                name = ARRAY_LVAL % count
                res += ' ' + name
                replacements[name] = e
                count += 1
            else:  # pseudo array. But pseudo array can contain true array. for example a[['d'][3]] has 2 pseudo and 1 true array
                cand, new_replacements, count = remove_arrays(e[1:-1], count)
                res += '[%s]' % cand
                replacements.update(new_replacements)
        else:
            res += e
        last = e
    return res, replacements, count


def translate_object(obj, lval, obj_count=1, arr_count=1):
    obj = obj[1:-1]  # remove {} from both ends
    obj, obj_rep, obj_count = remove_objects(obj, obj_count)
    obj, arr_rep, arr_count = remove_arrays(obj, arr_count)
    # functions can be defined inside objects. exp translator cant translate them.
    # we have to remove them and translate with func translator
    # its better explained in translate_array function
    obj, hoisted, inline = functions.remove_functions(obj, all_inline=True)
    assert not hoisted
    gsetters_after = ''
    keys = argsplit(obj)
    res = []
    for i, e in enumerate(keys, 1):
        e = e.strip()
        if e.startswith('set '):
            gsetters_after += translate_setter(lval, e)
        elif e.startswith('get '):
            gsetters_after += translate_getter(lval, e)
        elif ':' not in e:
            if i < len(keys
                       ):  # can happen legally only in the last element {3:2,}
                raise SyntaxError('Unexpected "," in Object literal')
            break
        else:  #Not getter, setter or elision
            spl = argsplit(e, ':')
            if len(spl) < 2:
                raise SyntaxError('Invalid Object literal: ' + e)
            try:
                key, value = spl
            except:  #len(spl)> 2
                print('Unusual case ' + repr(e))
                key = spl[0]
                value = ':'.join(spl[1:])
            key = key.strip()
            if is_internal(key):
                key = '%s.to_string().value' % key
            else:
                key = repr(key)

            value = exp_translator(value)
            if not value:
                raise SyntaxError('Missing value in Object literal')
            res.append('%s:%s' % (key, value))
    res = '%s = Js({%s})\n' % (lval, ','.join(res)) + gsetters_after
    # translate all the nested objects (including removed earlier functions)
    for nested_name, nested_info in inline.iteritems():  # functions
        nested_block, nested_args = nested_info
        new_def = FUNC_TRANSLATOR(nested_name, nested_block, nested_args)
        res = new_def + res
    for lval, obj in obj_rep.iteritems():  #objects
        new_def, obj_count, arr_count = translate_object(
            obj, lval, obj_count, arr_count)
        # add object definition BEFORE array definition
        res = new_def + res
    for lval, obj in arr_rep.iteritems():  # arrays
        new_def, obj_count, arr_count = translate_array(
            obj, lval, obj_count, arr_count)
        # add object definition BEFORE array definition
        res = new_def + res
    return res, obj_count, arr_count


def translate_setter(lval, setter):
    func = 'function' + setter[3:]
    try:
        _, data, _ = functions.remove_functions(func)
        if not data or len(data) > 1:
            raise Exception()
    except:
        raise SyntaxError('Could not parse setter: ' + setter)
    prop = data.keys()[0]
    body, args = data[prop]
    if len(args) != 1:  #setter must have exactly 1 argument
        raise SyntaxError('Invalid setter. It must take exactly 1 argument.')
    # now messy part
    res = FUNC_TRANSLATOR('setter', body, args)
    res += "%s.define_own_property(%s, {'set': setter})\n" % (lval, repr(prop))
    return res


def translate_getter(lval, getter):
    func = 'function' + getter[3:]
    try:
        _, data, _ = functions.remove_functions(func)
        if not data or len(data) > 1:
            raise Exception()
    except:
        raise SyntaxError('Could not parse getter: ' + getter)
    prop = data.keys()[0]
    body, args = data[prop]
    if len(args) != 0:  #setter must have exactly 0 argument
        raise SyntaxError('Invalid getter. It must take exactly 0 argument.')
    # now messy part
    res = FUNC_TRANSLATOR('getter', body, args)
    res += "%s.define_own_property(%s, {'get': setter})\n" % (lval, repr(prop))
    return res


def translate_array(array, lval, obj_count=1, arr_count=1):
    """array has to be any js array for example [1,2,3]
       lval has to be name of this array.
       Returns python code that adds lval to the PY scope it should be put before lval"""
    array = array[1:-1]
    array, obj_rep, obj_count = remove_objects(array, obj_count)
    array, arr_rep, arr_count = remove_arrays(array, arr_count)
    #functions can be also defined in arrays, this caused many problems since in Python
    # functions cant be defined inside literal
    # remove functions (they dont contain arrays or objects so can be translated easily)
    # hoisted functions are treated like inline
    array, hoisted, inline = functions.remove_functions(array, all_inline=True)
    assert not hoisted
    arr = []
    # separate elements in array
    for e in argsplit(array, ','):
        # translate expressions in array PyJsLvalInline will not be translated!
        e = exp_translator(e.replace('\n', ''))
        arr.append(e if e else 'None')
    arr = '%s = Js([%s])\n' % (lval, ','.join(arr))
    #But we can have more code to add to define arrays/objects/functions defined inside this array
    # translate nested objects:
    # functions:
    for nested_name, nested_info in inline.iteritems():
        nested_block, nested_args = nested_info
        new_def = FUNC_TRANSLATOR(nested_name, nested_block, nested_args)
        arr = new_def + arr
    for lval, obj in obj_rep.iteritems():
        new_def, obj_count, arr_count = translate_object(
            obj, lval, obj_count, arr_count)
        # add object definition BEFORE array definition
        arr = new_def + arr
    for lval, obj in arr_rep.iteritems():
        new_def, obj_count, arr_count = translate_array(
            obj, lval, obj_count, arr_count)
        # add object definition BEFORE array definition
        arr = new_def + arr
    return arr, obj_count, arr_count


if __name__ == '__main__':
    test = 'a = {404:{494:19}}; b = 303; if () {f={:}; {     }}'

    #print remove_objects(test)
    #print list(bracket_split(' {}'))
    print()
    print(remove_arrays(
        'typeof a&&!db.test(a)&&!ib[(bb.exec(a)||["",""], [][[5][5]])[1].toLowerCase()])'
    ))
    print(is_object('', ')'))
