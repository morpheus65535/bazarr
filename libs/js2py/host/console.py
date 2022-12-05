from ..base import *

@Js
def console():
    pass

@Js
def log():
    print(" ".join(repr(element) for element in arguments.to_list()))

console.put('log', log)
console.put('debug', log)
console.put('info', log)
console.put('warn', log)
console.put('error', log)
