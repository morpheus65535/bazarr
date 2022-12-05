from __future__ import print_function

from flow import translate_flow
from constants import remove_constants, recover_constants
from objects import remove_objects, remove_arrays, translate_object, translate_array, set_func_translator
from functions import remove_functions, reset_inline_count
from jsparser import inject_before_lval, indent, dbg

TOP_GLOBAL = '''from js2py.pyjs import *\nvar = Scope( JS_BUILTINS )\nset_global_object(var)\n'''


def translate_js(js, top=TOP_GLOBAL):
    """js has to be a javascript source code.
       returns equivalent python code."""
    # Remove constant literals
    no_const, constants = remove_constants(js)
    #print 'const count', len(constants)
    # Remove object literals
    no_obj, objects, obj_count = remove_objects(no_const)
    #print 'obj count', len(objects)
    # Remove arrays
    no_arr, arrays, arr_count = remove_arrays(no_obj)
    #print 'arr count', len(arrays)
    # Here remove and replace functions
    reset_inline_count()
    no_func, hoisted, inline = remove_functions(no_arr)

    #translate flow and expressions
    py_seed, to_register = translate_flow(no_func)

    # register variables and hoisted functions
    #top += '# register variables\n'
    top += 'var.registers(%s)\n' % str(to_register + hoisted.keys())

    #Recover functions
    # hoisted functions recovery
    defs = ''
    #defs += '# define hoisted functions\n'
    #print len(hoisted) , 'HH'*40
    for nested_name, nested_info in hoisted.iteritems():
        nested_block, nested_args = nested_info
        new_code = translate_func('PyJsLvalTempHoisted', nested_block,
                                  nested_args)
        new_code += 'PyJsLvalTempHoisted.func_name = %s\n' % repr(nested_name)
        defs += new_code + '\nvar.put(%s, PyJsLvalTempHoisted)\n' % repr(
            nested_name)
    #defs += '# Everting ready!\n'
    # inline functions recovery
    for nested_name, nested_info in inline.iteritems():
        nested_block, nested_args = nested_info
        new_code = translate_func(nested_name, nested_block, nested_args)
        py_seed = inject_before_lval(py_seed,
                                     nested_name.split('@')[0], new_code)
    # add hoisted definitiond - they have literals that have to be recovered
    py_seed = defs + py_seed

    #Recover arrays
    for arr_lval, arr_code in arrays.iteritems():
        translation, obj_count, arr_count = translate_array(
            arr_code, arr_lval, obj_count, arr_count)
        py_seed = inject_before_lval(py_seed, arr_lval, translation)

    #Recover objects
    for obj_lval, obj_code in objects.iteritems():
        translation, obj_count, arr_count = translate_object(
            obj_code, obj_lval, obj_count, arr_count)
        py_seed = inject_before_lval(py_seed, obj_lval, translation)

    #Recover constants
    py_code = recover_constants(py_seed, constants)

    return top + py_code


def translate_func(name, block, args):
    """Translates functions and all nested functions to Python code.
       name -  name of that function (global functions will be available under var while
            inline will be available directly under this name )
       block - code of the function (*with* brackets {} )
       args - arguments that this function takes"""
    inline = name.startswith('PyJsLvalInline')
    real_name = ''
    if inline:
        name, real_name = name.split('@')
    arglist = ', '.join(args) + ', ' if args else ''
    code = '@Js\ndef %s(%sthis, arguments, var=var):\n' % (name, arglist)
    # register local variables
    scope = "'this':this, 'arguments':arguments"  #it will be a simple dictionary
    for arg in args:
        scope += ', %s:%s' % (repr(arg), arg)
    if real_name:
        scope += ', %s:%s' % (repr(real_name), name)
    code += indent('var = Scope({%s}, var)\n' % scope)
    block, nested_hoisted, nested_inline = remove_functions(block)
    py_code, to_register = translate_flow(block)
    #register variables declared with var and names of hoisted functions.
    to_register += nested_hoisted.keys()
    if to_register:
        code += indent('var.registers(%s)\n' % str(to_register))
    for nested_name, info in nested_hoisted.iteritems():
        nested_block, nested_args = info
        new_code = translate_func('PyJsLvalTempHoisted', nested_block,
                                  nested_args)
        # Now put definition of hoisted function on the top
        code += indent(new_code)
        code += indent(
            'PyJsLvalTempHoisted.func_name = %s\n' % repr(nested_name))
        code += indent(
            'var.put(%s, PyJsLvalTempHoisted)\n' % repr(nested_name))
    for nested_name, info in nested_inline.iteritems():
        nested_block, nested_args = info
        new_code = translate_func(nested_name, nested_block, nested_args)
        # Inject definitions of inline functions just before usage
        # nested inline names have this format : LVAL_NAME@REAL_NAME
        py_code = inject_before_lval(py_code,
                                     nested_name.split('@')[0], new_code)
    if py_code.strip():
        code += indent(py_code)
    return code


set_func_translator(translate_func)

#print inject_before_lval('   chuj\n   moj\n   lval\nelse\n', 'lval', 'siema\njestem piter\n')
import time
#print time.time()
#print translate_js('if (1) console.log("Hello, World!"); else if (5) console.log("Hello world?");')
#print time.time()
t = """
var x = [1,2,3,4,5,6];
for (var e in x) {console.log(e); delete x[3];}
console.log(5 in [1,2,3,4,5]);

"""

SANDBOX = '''
import traceback
try:
%s
except:
    print traceback.format_exc()
print
raw_input('Press Enter to quit')
'''
if __name__ == '__main__':
    # test with jq if works then it really works :)
    #with open('jq.js', 'r') as f:
    #jq = f.read()

    #res = translate_js(jq)
    res = translate_js(t)
    dbg(SANDBOX % indent(res))
    print('Done')
