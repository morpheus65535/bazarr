from internals import byte_trans
from internals import seval
import pyjsparser

x = r'''
function g() {var h123 = 11; return [function g1() {return h123}, new Function('return h123')]}
g()[1]()
'''
print seval.eval_js_vm(x)
