# JUST FOR NOW, later I will write my own - much faster and better.

#  Copyright (C) 2013 Ariya Hidayat <ariya.hidayat@gmail.com>
#  Copyright (C) 2013 Thaddee Tyl <thaddee.tyl@gmail.com>
#  Copyright (C) 2012 Ariya Hidayat <ariya.hidayat@gmail.com>
#  Copyright (C) 2012 Mathias Bynens <mathias@qiwi.be>
#  Copyright (C) 2012 Joost-Wim Boekesteijn <joost-wim@boekesteijn.nl>
#  Copyright (C) 2012 Kris Kowal <kris.kowal@cixar.com>
#  Copyright (C) 2012 Yusuke Suzuki <utatane.tea@gmail.com>
#  Copyright (C) 2012 Arpad Borsos <arpad.borsos@googlemail.com>
#  Copyright (C) 2011 Ariya Hidayat <ariya.hidayat@gmail.com>
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
#  THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# -*- coding: latin-1 -*-
from __future__ import print_function
import re


def typeof(t):
    if t is None: return 'undefined'
    elif isinstance(t, bool): return 'boolean'
    elif isinstance(t, str): return 'string'
    elif isinstance(t, int) or isinstance(t, float): return 'number'
    elif hasattr(t, '__call__'): return 'function'
    else: return 'object'


def list_indexOf(l, v):
    try:
        return l.index(v)
    except:
        return -1


parseFloat = float
parseInt = int


class jsdict(object):
    def __init__(self, d):
        self.__dict__.update(d)

    def __getitem__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return None

    def __setitem__(self, name, value):
        self.__dict__[name] = value
        return value

    def __getattr__(self, name):
        try:
            return getattr(self, name)
        except:
            return None

    def __setattr__(self, name, value):
        self[name] = value
        return value

    def __contains__(self, name):
        return name in self.__dict__

    def __repr__(self):
        return str(self.__dict__)


class RegExp(object):
    def __init__(self, pattern, flags=''):
        self.flags = flags
        pyflags = 0 | re.M if 'm' in flags else 0 | re.I if 'i' in flags else 0
        self.source = pattern
        self.pattern = re.compile(pattern, pyflags)

    def test(self, s):
        return self.pattern.search(s) is not None


console = jsdict({"log": print})


def __temp__42(object=None, body=None):
    return jsdict({
        "type": Syntax.WithStatement,
        "object": object,
        "body": body,
    })


def __temp__41(test=None, body=None):
    return jsdict({
        "type": Syntax.WhileStatement,
        "test": test,
        "body": body,
    })


def __temp__40(id=None, init=None):
    return jsdict({
        "type": Syntax.VariableDeclarator,
        "id": id,
        "init": init,
    })


def __temp__39(declarations=None, kind=None):
    return jsdict({
        "type": Syntax.VariableDeclaration,
        "declarations": declarations,
        "kind": kind,
    })


def __temp__38(operator=None, argument=None):
    if (operator == "++") or (operator == "--"):
        return jsdict({
            "type": Syntax.UpdateExpression,
            "operator": operator,
            "argument": argument,
            "prefix": True,
        })
    return jsdict({
        "type": Syntax.UnaryExpression,
        "operator": operator,
        "argument": argument,
        "prefix": True,
    })


def __temp__37(block=None, guardedHandlers=None, handlers=None,
               finalizer=None):
    return jsdict({
        "type": Syntax.TryStatement,
        "block": block,
        "guardedHandlers": guardedHandlers,
        "handlers": handlers,
        "finalizer": finalizer,
    })


def __temp__36(argument=None):
    return jsdict({
        "type": Syntax.ThrowStatement,
        "argument": argument,
    })


def __temp__35():
    return jsdict({
        "type": Syntax.ThisExpression,
    })


def __temp__34(discriminant=None, cases=None):
    return jsdict({
        "type": Syntax.SwitchStatement,
        "discriminant": discriminant,
        "cases": cases,
    })


def __temp__33(test=None, consequent=None):
    return jsdict({
        "type": Syntax.SwitchCase,
        "test": test,
        "consequent": consequent,
    })


def __temp__32(expressions=None):
    return jsdict({
        "type": Syntax.SequenceExpression,
        "expressions": expressions,
    })


def __temp__31(argument=None):
    return jsdict({
        "type": Syntax.ReturnStatement,
        "argument": argument,
    })


def __temp__30(kind=None, key=None, value=None):
    return jsdict({
        "type": Syntax.Property,
        "key": key,
        "value": value,
        "kind": kind,
    })


def __temp__29(body=None):
    return jsdict({
        "type": Syntax.Program,
        "body": body,
    })


def __temp__28(operator=None, argument=None):
    return jsdict({
        "type": Syntax.UpdateExpression,
        "operator": operator,
        "argument": argument,
        "prefix": False,
    })


def __temp__27(properties=None):
    return jsdict({
        "type": Syntax.ObjectExpression,
        "properties": properties,
    })


def __temp__26(callee=None, args=None):
    return jsdict({
        "type": Syntax.NewExpression,
        "callee": callee,
        "arguments": args,
    })


def __temp__25(accessor=None, object=None, property=None):
    return jsdict({
        "type": Syntax.MemberExpression,
        "computed": accessor == "[",
        "object": object,
        "property": property,
    })


def __temp__24(token=None):
    return jsdict({
        "type": Syntax.Literal,
        "value": token.value,
        "raw": source[token.range[0]:token.range[1]],
    })


def __temp__23(label=None, body=None):
    return jsdict({
        "type": Syntax.LabeledStatement,
        "label": label,
        "body": body,
    })


def __temp__22(test=None, consequent=None, alternate=None):
    return jsdict({
        "type": Syntax.IfStatement,
        "test": test,
        "consequent": consequent,
        "alternate": alternate,
    })


def __temp__21(name=None):
    return jsdict({
        "type": Syntax.Identifier,
        "name": name,
    })


def __temp__20(id=None, params=None, defaults=None, body=None):
    return jsdict({
        "type": Syntax.FunctionExpression,
        "id": id,
        "params": params,
        "defaults": defaults,
        "body": body,
        "rest": None,
        "generator": False,
        "expression": False,
    })


def __temp__19(id=None, params=None, defaults=None, body=None):
    return jsdict({
        "type": Syntax.FunctionDeclaration,
        "id": id,
        "params": params,
        "defaults": defaults,
        "body": body,
        "rest": None,
        "generator": False,
        "expression": False,
    })


def __temp__18(left=None, right=None, body=None):
    return jsdict({
        "type": Syntax.ForInStatement,
        "left": left,
        "right": right,
        "body": body,
        "each": False,
    })


def __temp__17(init=None, test=None, update=None, body=None):
    return jsdict({
        "type": Syntax.ForStatement,
        "init": init,
        "test": test,
        "update": update,
        "body": body,
    })


def __temp__16(expression=None):
    return jsdict({
        "type": Syntax.ExpressionStatement,
        "expression": expression,
    })


def __temp__15():
    return jsdict({
        "type": Syntax.EmptyStatement,
    })


def __temp__14(body=None, test=None):
    return jsdict({
        "type": Syntax.DoWhileStatement,
        "body": body,
        "test": test,
    })


def __temp__13():
    return jsdict({
        "type": Syntax.DebuggerStatement,
    })


def __temp__12(label=None):
    return jsdict({
        "type": Syntax.ContinueStatement,
        "label": label,
    })


def __temp__11(test=None, consequent=None, alternate=None):
    return jsdict({
        "type": Syntax.ConditionalExpression,
        "test": test,
        "consequent": consequent,
        "alternate": alternate,
    })


def __temp__10(param=None, body=None):
    return jsdict({
        "type": Syntax.CatchClause,
        "param": param,
        "body": body,
    })


def __temp__9(callee=None, args=None):
    return jsdict({
        "type": Syntax.CallExpression,
        "callee": callee,
        "arguments": args,
    })


def __temp__8(label=None):
    return jsdict({
        "type": Syntax.BreakStatement,
        "label": label,
    })


def __temp__7(body=None):
    return jsdict({
        "type": Syntax.BlockStatement,
        "body": body,
    })


def __temp__6(operator=None, left=None, right=None):
    type = (Syntax.LogicalExpression if (operator == "||") or
            (operator == "&&") else Syntax.BinaryExpression)
    return jsdict({
        "type": type,
        "operator": operator,
        "left": left,
        "right": right,
    })


def __temp__5(operator=None, left=None, right=None):
    return jsdict({
        "type": Syntax.AssignmentExpression,
        "operator": operator,
        "left": left,
        "right": right,
    })


def __temp__4(elements=None):
    return jsdict({
        "type": Syntax.ArrayExpression,
        "elements": elements,
    })


def __temp__3(node=None):
    if extra.source:
        node.loc.source = extra.source
    return node


def __temp__2(node=None):
    if node.range or node.loc:
        if extra.loc:
            state.markerStack.pop()
            state.markerStack.pop()
        if extra.range:
            state.markerStack.pop()
    else:
        SyntaxTreeDelegate.markEnd(node)
    return node


def __temp__1(node=None):
    if extra.range:
        node.range = [state.markerStack.pop(), index]
    if extra.loc:
        node.loc = jsdict({
            "start":
            jsdict({
                "line": state.markerStack.pop(),
                "column": state.markerStack.pop(),
            }),
            "end":
            jsdict({
                "line": lineNumber,
                "column": index - lineStart,
            }),
        })
        SyntaxTreeDelegate.postProcess(node)
    return node


def __temp__0():
    if extra.loc:
        state.markerStack.append(index - lineStart)
        state.markerStack.append(lineNumber)
    if extra.range:
        state.markerStack.append(index)


Token = None
TokenName = None
FnExprTokens = None
Syntax = None
PropertyKind = None
Messages = None
Regex = None
SyntaxTreeDelegate = None
source = None
strict = None
index = None
lineNumber = None
lineStart = None
length = None
delegate = None
lookahead = None
state = None
extra = None
Token = jsdict({
    "BooleanLiteral": 1,
    "EOF": 2,
    "Identifier": 3,
    "Keyword": 4,
    "NullLiteral": 5,
    "NumericLiteral": 6,
    "Punctuator": 7,
    "StringLiteral": 8,
    "RegularExpression": 9,
})
TokenName = jsdict({})
TokenName[Token.BooleanLiteral] = "Boolean"
TokenName[Token.EOF] = "<end>"
TokenName[Token.Identifier] = "Identifier"
TokenName[Token.Keyword] = "Keyword"
TokenName[Token.NullLiteral] = "Null"
TokenName[Token.NumericLiteral] = "Numeric"
TokenName[Token.Punctuator] = "Punctuator"
TokenName[Token.StringLiteral] = "String"
TokenName[Token.RegularExpression] = "RegularExpression"
FnExprTokens = [
    "(", "{", "[", "in", "typeof", "instanceof", "new", "return", "case",
    "delete", "throw", "void", "=", "+=", "-=", "*=", "/=", "%=", "<<=", ">>=",
    ">>>=", "&=", "|=", "^=", ",", "+", "-", "*", "/", "%", "++", "--", "<<",
    ">>", ">>>", "&", "|", "^", "!", "~", "&&", "||", "?", ":", "===", "==",
    ">=", "<=", "<", ">", "!=", "!=="
]
Syntax = jsdict({
    "AssignmentExpression": "AssignmentExpression",
    "ArrayExpression": "ArrayExpression",
    "BlockStatement": "BlockStatement",
    "BinaryExpression": "BinaryExpression",
    "BreakStatement": "BreakStatement",
    "CallExpression": "CallExpression",
    "CatchClause": "CatchClause",
    "ConditionalExpression": "ConditionalExpression",
    "ContinueStatement": "ContinueStatement",
    "DoWhileStatement": "DoWhileStatement",
    "DebuggerStatement": "DebuggerStatement",
    "EmptyStatement": "EmptyStatement",
    "ExpressionStatement": "ExpressionStatement",
    "ForStatement": "ForStatement",
    "ForInStatement": "ForInStatement",
    "FunctionDeclaration": "FunctionDeclaration",
    "FunctionExpression": "FunctionExpression",
    "Identifier": "Identifier",
    "IfStatement": "IfStatement",
    "Literal": "Literal",
    "LabeledStatement": "LabeledStatement",
    "LogicalExpression": "LogicalExpression",
    "MemberExpression": "MemberExpression",
    "NewExpression": "NewExpression",
    "ObjectExpression": "ObjectExpression",
    "Program": "Program",
    "Property": "Property",
    "ReturnStatement": "ReturnStatement",
    "SequenceExpression": "SequenceExpression",
    "SwitchStatement": "SwitchStatement",
    "SwitchCase": "SwitchCase",
    "ThisExpression": "ThisExpression",
    "ThrowStatement": "ThrowStatement",
    "TryStatement": "TryStatement",
    "UnaryExpression": "UnaryExpression",
    "UpdateExpression": "UpdateExpression",
    "VariableDeclaration": "VariableDeclaration",
    "VariableDeclarator": "VariableDeclarator",
    "WhileStatement": "WhileStatement",
    "WithStatement": "WithStatement",
})
PropertyKind = jsdict({
    "Data": 1,
    "Get": 2,
    "Set": 4,
})
Messages = jsdict({
    "UnexpectedToken":
    "Unexpected token %0",
    "UnexpectedNumber":
    "Unexpected number",
    "UnexpectedString":
    "Unexpected string",
    "UnexpectedIdentifier":
    "Unexpected identifier",
    "UnexpectedReserved":
    "Unexpected reserved word",
    "UnexpectedEOS":
    "Unexpected end of input",
    "NewlineAfterThrow":
    "Illegal newline after throw",
    "InvalidRegExp":
    "Invalid regular expression",
    "UnterminatedRegExp":
    "Invalid regular expression: missing /",
    "InvalidLHSInAssignment":
    "Invalid left-hand side in assignment",
    "InvalidLHSInForIn":
    "Invalid left-hand side in for-in",
    "MultipleDefaultsInSwitch":
    "More than one default clause in switch statement",
    "NoCatchOrFinally":
    "Missing catch or finally after try",
    "UnknownLabel":
    "Undefined label '%0'",
    "Redeclaration":
    "%0 '%1' has already been declared",
    "IllegalContinue":
    "Illegal continue statement",
    "IllegalBreak":
    "Illegal break statement",
    "IllegalReturn":
    "Illegal return statement",
    "StrictModeWith":
    "Strict mode code may not include a with statement",
    "StrictCatchVariable":
    "Catch variable may not be eval or arguments in strict mode",
    "StrictVarName":
    "Variable name may not be eval or arguments in strict mode",
    "StrictParamName":
    "Parameter name eval or arguments is not allowed in strict mode",
    "StrictParamDupe":
    "Strict mode function may not have duplicate parameter names",
    "StrictFunctionName":
    "Function name may not be eval or arguments in strict mode",
    "StrictOctalLiteral":
    "Octal literals are not allowed in strict mode.",
    "StrictDelete":
    "Delete of an unqualified identifier in strict mode.",
    "StrictDuplicateProperty":
    "Duplicate data property in object literal not allowed in strict mode",
    "AccessorDataProperty":
    "Object literal may not have data and accessor property with the same name",
    "AccessorGetSet":
    "Object literal may not have multiple get/set accessors with the same name",
    "StrictLHSAssignment":
    "Assignment to eval or arguments is not allowed in strict mode",
    "StrictLHSPostfix":
    "Postfix increment/decrement may not have eval or arguments operand in strict mode",
    "StrictLHSPrefix":
    "Prefix increment/decrement may not have eval or arguments operand in strict mode",
    "StrictReservedWord":
    "Use of future reserved word in strict mode",
})
Regex = jsdict({
    "NonAsciiIdentifierStart":
    RegExp(
        u"[\xaa\xb5\xba\xc0-\xd6\xd8-\xf6\xf8-\u02c1\u02c6-\u02d1\u02e0-\u02e4\u02ec\u02ee\u0370-\u0374\u0376\u0377\u037a-\u037d\u0386\u0388-\u038a\u038c\u038e-\u03a1\u03a3-\u03f5\u03f7-\u0481\u048a-\u0527\u0531-\u0556\u0559\u0561-\u0587\u05d0-\u05ea\u05f0-\u05f2\u0620-\u064a\u066e\u066f\u0671-\u06d3\u06d5\u06e5\u06e6\u06ee\u06ef\u06fa-\u06fc\u06ff\u0710\u0712-\u072f\u074d-\u07a5\u07b1\u07ca-\u07ea\u07f4\u07f5\u07fa\u0800-\u0815\u081a\u0824\u0828\u0840-\u0858\u08a0\u08a2-\u08ac\u0904-\u0939\u093d\u0950\u0958-\u0961\u0971-\u0977\u0979-\u097f\u0985-\u098c\u098f\u0990\u0993-\u09a8\u09aa-\u09b0\u09b2\u09b6-\u09b9\u09bd\u09ce\u09dc\u09dd\u09df-\u09e1\u09f0\u09f1\u0a05-\u0a0a\u0a0f\u0a10\u0a13-\u0a28\u0a2a-\u0a30\u0a32\u0a33\u0a35\u0a36\u0a38\u0a39\u0a59-\u0a5c\u0a5e\u0a72-\u0a74\u0a85-\u0a8d\u0a8f-\u0a91\u0a93-\u0aa8\u0aaa-\u0ab0\u0ab2\u0ab3\u0ab5-\u0ab9\u0abd\u0ad0\u0ae0\u0ae1\u0b05-\u0b0c\u0b0f\u0b10\u0b13-\u0b28\u0b2a-\u0b30\u0b32\u0b33\u0b35-\u0b39\u0b3d\u0b5c\u0b5d\u0b5f-\u0b61\u0b71\u0b83\u0b85-\u0b8a\u0b8e-\u0b90\u0b92-\u0b95\u0b99\u0b9a\u0b9c\u0b9e\u0b9f\u0ba3\u0ba4\u0ba8-\u0baa\u0bae-\u0bb9\u0bd0\u0c05-\u0c0c\u0c0e-\u0c10\u0c12-\u0c28\u0c2a-\u0c33\u0c35-\u0c39\u0c3d\u0c58\u0c59\u0c60\u0c61\u0c85-\u0c8c\u0c8e-\u0c90\u0c92-\u0ca8\u0caa-\u0cb3\u0cb5-\u0cb9\u0cbd\u0cde\u0ce0\u0ce1\u0cf1\u0cf2\u0d05-\u0d0c\u0d0e-\u0d10\u0d12-\u0d3a\u0d3d\u0d4e\u0d60\u0d61\u0d7a-\u0d7f\u0d85-\u0d96\u0d9a-\u0db1\u0db3-\u0dbb\u0dbd\u0dc0-\u0dc6\u0e01-\u0e30\u0e32\u0e33\u0e40-\u0e46\u0e81\u0e82\u0e84\u0e87\u0e88\u0e8a\u0e8d\u0e94-\u0e97\u0e99-\u0e9f\u0ea1-\u0ea3\u0ea5\u0ea7\u0eaa\u0eab\u0ead-\u0eb0\u0eb2\u0eb3\u0ebd\u0ec0-\u0ec4\u0ec6\u0edc-\u0edf\u0f00\u0f40-\u0f47\u0f49-\u0f6c\u0f88-\u0f8c\u1000-\u102a\u103f\u1050-\u1055\u105a-\u105d\u1061\u1065\u1066\u106e-\u1070\u1075-\u1081\u108e\u10a0-\u10c5\u10c7\u10cd\u10d0-\u10fa\u10fc-\u1248\u124a-\u124d\u1250-\u1256\u1258\u125a-\u125d\u1260-\u1288\u128a-\u128d\u1290-\u12b0\u12b2-\u12b5\u12b8-\u12be\u12c0\u12c2-\u12c5\u12c8-\u12d6\u12d8-\u1310\u1312-\u1315\u1318-\u135a\u1380-\u138f\u13a0-\u13f4\u1401-\u166c\u166f-\u167f\u1681-\u169a\u16a0-\u16ea\u16ee-\u16f0\u1700-\u170c\u170e-\u1711\u1720-\u1731\u1740-\u1751\u1760-\u176c\u176e-\u1770\u1780-\u17b3\u17d7\u17dc\u1820-\u1877\u1880-\u18a8\u18aa\u18b0-\u18f5\u1900-\u191c\u1950-\u196d\u1970-\u1974\u1980-\u19ab\u19c1-\u19c7\u1a00-\u1a16\u1a20-\u1a54\u1aa7\u1b05-\u1b33\u1b45-\u1b4b\u1b83-\u1ba0\u1bae\u1baf\u1bba-\u1be5\u1c00-\u1c23\u1c4d-\u1c4f\u1c5a-\u1c7d\u1ce9-\u1cec\u1cee-\u1cf1\u1cf5\u1cf6\u1d00-\u1dbf\u1e00-\u1f15\u1f18-\u1f1d\u1f20-\u1f45\u1f48-\u1f4d\u1f50-\u1f57\u1f59\u1f5b\u1f5d\u1f5f-\u1f7d\u1f80-\u1fb4\u1fb6-\u1fbc\u1fbe\u1fc2-\u1fc4\u1fc6-\u1fcc\u1fd0-\u1fd3\u1fd6-\u1fdb\u1fe0-\u1fec\u1ff2-\u1ff4\u1ff6-\u1ffc\u2071\u207f\u2090-\u209c\u2102\u2107\u210a-\u2113\u2115\u2119-\u211d\u2124\u2126\u2128\u212a-\u212d\u212f-\u2139\u213c-\u213f\u2145-\u2149\u214e\u2160-\u2188\u2c00-\u2c2e\u2c30-\u2c5e\u2c60-\u2ce4\u2ceb-\u2cee\u2cf2\u2cf3\u2d00-\u2d25\u2d27\u2d2d\u2d30-\u2d67\u2d6f\u2d80-\u2d96\u2da0-\u2da6\u2da8-\u2dae\u2db0-\u2db6\u2db8-\u2dbe\u2dc0-\u2dc6\u2dc8-\u2dce\u2dd0-\u2dd6\u2dd8-\u2dde\u2e2f\u3005-\u3007\u3021-\u3029\u3031-\u3035\u3038-\u303c\u3041-\u3096\u309d-\u309f\u30a1-\u30fa\u30fc-\u30ff\u3105-\u312d\u3131-\u318e\u31a0-\u31ba\u31f0-\u31ff\u3400-\u4db5\u4e00-\u9fcc\ua000-\ua48c\ua4d0-\ua4fd\ua500-\ua60c\ua610-\ua61f\ua62a\ua62b\ua640-\ua66e\ua67f-\ua697\ua6a0-\ua6ef\ua717-\ua71f\ua722-\ua788\ua78b-\ua78e\ua790-\ua793\ua7a0-\ua7aa\ua7f8-\ua801\ua803-\ua805\ua807-\ua80a\ua80c-\ua822\ua840-\ua873\ua882-\ua8b3\ua8f2-\ua8f7\ua8fb\ua90a-\ua925\ua930-\ua946\ua960-\ua97c\ua984-\ua9b2\ua9cf\uaa00-\uaa28\uaa40-\uaa42\uaa44-\uaa4b\uaa60-\uaa76\uaa7a\uaa80-\uaaaf\uaab1\uaab5\uaab6\uaab9-\uaabd\uaac0\uaac2\uaadb-\uaadd\uaae0-\uaaea\uaaf2-\uaaf4\uab01-\uab06\uab09-\uab0e\uab11-\uab16\uab20-\uab26\uab28-\uab2e\uabc0-\uabe2\uac00-\ud7a3\ud7b0-\ud7c6\ud7cb-\ud7fb\uf900-\ufa6d\ufa70-\ufad9\ufb00-\ufb06\ufb13-\ufb17\ufb1d\ufb1f-\ufb28\ufb2a-\ufb36\ufb38-\ufb3c\ufb3e\ufb40\ufb41\ufb43\ufb44\ufb46-\ufbb1\ufbd3-\ufd3d\ufd50-\ufd8f\ufd92-\ufdc7\ufdf0-\ufdfb\ufe70-\ufe74\ufe76-\ufefc\uff21-\uff3a\uff41-\uff5a\uff66-\uffbe\uffc2-\uffc7\uffca-\uffcf\uffd2-\uffd7\uffda-\uffdc]"
    ),
    "NonAsciiIdentifierPart":
    RegExp(
        u"[\xaa\xb5\xba\xc0-\xd6\xd8-\xf6\xf8-\u02c1\u02c6-\u02d1\u02e0-\u02e4\u02ec\u02ee\u0300-\u0374\u0376\u0377\u037a-\u037d\u0386\u0388-\u038a\u038c\u038e-\u03a1\u03a3-\u03f5\u03f7-\u0481\u0483-\u0487\u048a-\u0527\u0531-\u0556\u0559\u0561-\u0587\u0591-\u05bd\u05bf\u05c1\u05c2\u05c4\u05c5\u05c7\u05d0-\u05ea\u05f0-\u05f2\u0610-\u061a\u0620-\u0669\u066e-\u06d3\u06d5-\u06dc\u06df-\u06e8\u06ea-\u06fc\u06ff\u0710-\u074a\u074d-\u07b1\u07c0-\u07f5\u07fa\u0800-\u082d\u0840-\u085b\u08a0\u08a2-\u08ac\u08e4-\u08fe\u0900-\u0963\u0966-\u096f\u0971-\u0977\u0979-\u097f\u0981-\u0983\u0985-\u098c\u098f\u0990\u0993-\u09a8\u09aa-\u09b0\u09b2\u09b6-\u09b9\u09bc-\u09c4\u09c7\u09c8\u09cb-\u09ce\u09d7\u09dc\u09dd\u09df-\u09e3\u09e6-\u09f1\u0a01-\u0a03\u0a05-\u0a0a\u0a0f\u0a10\u0a13-\u0a28\u0a2a-\u0a30\u0a32\u0a33\u0a35\u0a36\u0a38\u0a39\u0a3c\u0a3e-\u0a42\u0a47\u0a48\u0a4b-\u0a4d\u0a51\u0a59-\u0a5c\u0a5e\u0a66-\u0a75\u0a81-\u0a83\u0a85-\u0a8d\u0a8f-\u0a91\u0a93-\u0aa8\u0aaa-\u0ab0\u0ab2\u0ab3\u0ab5-\u0ab9\u0abc-\u0ac5\u0ac7-\u0ac9\u0acb-\u0acd\u0ad0\u0ae0-\u0ae3\u0ae6-\u0aef\u0b01-\u0b03\u0b05-\u0b0c\u0b0f\u0b10\u0b13-\u0b28\u0b2a-\u0b30\u0b32\u0b33\u0b35-\u0b39\u0b3c-\u0b44\u0b47\u0b48\u0b4b-\u0b4d\u0b56\u0b57\u0b5c\u0b5d\u0b5f-\u0b63\u0b66-\u0b6f\u0b71\u0b82\u0b83\u0b85-\u0b8a\u0b8e-\u0b90\u0b92-\u0b95\u0b99\u0b9a\u0b9c\u0b9e\u0b9f\u0ba3\u0ba4\u0ba8-\u0baa\u0bae-\u0bb9\u0bbe-\u0bc2\u0bc6-\u0bc8\u0bca-\u0bcd\u0bd0\u0bd7\u0be6-\u0bef\u0c01-\u0c03\u0c05-\u0c0c\u0c0e-\u0c10\u0c12-\u0c28\u0c2a-\u0c33\u0c35-\u0c39\u0c3d-\u0c44\u0c46-\u0c48\u0c4a-\u0c4d\u0c55\u0c56\u0c58\u0c59\u0c60-\u0c63\u0c66-\u0c6f\u0c82\u0c83\u0c85-\u0c8c\u0c8e-\u0c90\u0c92-\u0ca8\u0caa-\u0cb3\u0cb5-\u0cb9\u0cbc-\u0cc4\u0cc6-\u0cc8\u0cca-\u0ccd\u0cd5\u0cd6\u0cde\u0ce0-\u0ce3\u0ce6-\u0cef\u0cf1\u0cf2\u0d02\u0d03\u0d05-\u0d0c\u0d0e-\u0d10\u0d12-\u0d3a\u0d3d-\u0d44\u0d46-\u0d48\u0d4a-\u0d4e\u0d57\u0d60-\u0d63\u0d66-\u0d6f\u0d7a-\u0d7f\u0d82\u0d83\u0d85-\u0d96\u0d9a-\u0db1\u0db3-\u0dbb\u0dbd\u0dc0-\u0dc6\u0dca\u0dcf-\u0dd4\u0dd6\u0dd8-\u0ddf\u0df2\u0df3\u0e01-\u0e3a\u0e40-\u0e4e\u0e50-\u0e59\u0e81\u0e82\u0e84\u0e87\u0e88\u0e8a\u0e8d\u0e94-\u0e97\u0e99-\u0e9f\u0ea1-\u0ea3\u0ea5\u0ea7\u0eaa\u0eab\u0ead-\u0eb9\u0ebb-\u0ebd\u0ec0-\u0ec4\u0ec6\u0ec8-\u0ecd\u0ed0-\u0ed9\u0edc-\u0edf\u0f00\u0f18\u0f19\u0f20-\u0f29\u0f35\u0f37\u0f39\u0f3e-\u0f47\u0f49-\u0f6c\u0f71-\u0f84\u0f86-\u0f97\u0f99-\u0fbc\u0fc6\u1000-\u1049\u1050-\u109d\u10a0-\u10c5\u10c7\u10cd\u10d0-\u10fa\u10fc-\u1248\u124a-\u124d\u1250-\u1256\u1258\u125a-\u125d\u1260-\u1288\u128a-\u128d\u1290-\u12b0\u12b2-\u12b5\u12b8-\u12be\u12c0\u12c2-\u12c5\u12c8-\u12d6\u12d8-\u1310\u1312-\u1315\u1318-\u135a\u135d-\u135f\u1380-\u138f\u13a0-\u13f4\u1401-\u166c\u166f-\u167f\u1681-\u169a\u16a0-\u16ea\u16ee-\u16f0\u1700-\u170c\u170e-\u1714\u1720-\u1734\u1740-\u1753\u1760-\u176c\u176e-\u1770\u1772\u1773\u1780-\u17d3\u17d7\u17dc\u17dd\u17e0-\u17e9\u180b-\u180d\u1810-\u1819\u1820-\u1877\u1880-\u18aa\u18b0-\u18f5\u1900-\u191c\u1920-\u192b\u1930-\u193b\u1946-\u196d\u1970-\u1974\u1980-\u19ab\u19b0-\u19c9\u19d0-\u19d9\u1a00-\u1a1b\u1a20-\u1a5e\u1a60-\u1a7c\u1a7f-\u1a89\u1a90-\u1a99\u1aa7\u1b00-\u1b4b\u1b50-\u1b59\u1b6b-\u1b73\u1b80-\u1bf3\u1c00-\u1c37\u1c40-\u1c49\u1c4d-\u1c7d\u1cd0-\u1cd2\u1cd4-\u1cf6\u1d00-\u1de6\u1dfc-\u1f15\u1f18-\u1f1d\u1f20-\u1f45\u1f48-\u1f4d\u1f50-\u1f57\u1f59\u1f5b\u1f5d\u1f5f-\u1f7d\u1f80-\u1fb4\u1fb6-\u1fbc\u1fbe\u1fc2-\u1fc4\u1fc6-\u1fcc\u1fd0-\u1fd3\u1fd6-\u1fdb\u1fe0-\u1fec\u1ff2-\u1ff4\u1ff6-\u1ffc\u200c\u200d\u203f\u2040\u2054\u2071\u207f\u2090-\u209c\u20d0-\u20dc\u20e1\u20e5-\u20f0\u2102\u2107\u210a-\u2113\u2115\u2119-\u211d\u2124\u2126\u2128\u212a-\u212d\u212f-\u2139\u213c-\u213f\u2145-\u2149\u214e\u2160-\u2188\u2c00-\u2c2e\u2c30-\u2c5e\u2c60-\u2ce4\u2ceb-\u2cf3\u2d00-\u2d25\u2d27\u2d2d\u2d30-\u2d67\u2d6f\u2d7f-\u2d96\u2da0-\u2da6\u2da8-\u2dae\u2db0-\u2db6\u2db8-\u2dbe\u2dc0-\u2dc6\u2dc8-\u2dce\u2dd0-\u2dd6\u2dd8-\u2dde\u2de0-\u2dff\u2e2f\u3005-\u3007\u3021-\u302f\u3031-\u3035\u3038-\u303c\u3041-\u3096\u3099\u309a\u309d-\u309f\u30a1-\u30fa\u30fc-\u30ff\u3105-\u312d\u3131-\u318e\u31a0-\u31ba\u31f0-\u31ff\u3400-\u4db5\u4e00-\u9fcc\ua000-\ua48c\ua4d0-\ua4fd\ua500-\ua60c\ua610-\ua62b\ua640-\ua66f\ua674-\ua67d\ua67f-\ua697\ua69f-\ua6f1\ua717-\ua71f\ua722-\ua788\ua78b-\ua78e\ua790-\ua793\ua7a0-\ua7aa\ua7f8-\ua827\ua840-\ua873\ua880-\ua8c4\ua8d0-\ua8d9\ua8e0-\ua8f7\ua8fb\ua900-\ua92d\ua930-\ua953\ua960-\ua97c\ua980-\ua9c0\ua9cf-\ua9d9\uaa00-\uaa36\uaa40-\uaa4d\uaa50-\uaa59\uaa60-\uaa76\uaa7a\uaa7b\uaa80-\uaac2\uaadb-\uaadd\uaae0-\uaaef\uaaf2-\uaaf6\uab01-\uab06\uab09-\uab0e\uab11-\uab16\uab20-\uab26\uab28-\uab2e\uabc0-\uabea\uabec\uabed\uabf0-\uabf9\uac00-\ud7a3\ud7b0-\ud7c6\ud7cb-\ud7fb\uf900-\ufa6d\ufa70-\ufad9\ufb00-\ufb06\ufb13-\ufb17\ufb1d-\ufb28\ufb2a-\ufb36\ufb38-\ufb3c\ufb3e\ufb40\ufb41\ufb43\ufb44\ufb46-\ufbb1\ufbd3-\ufd3d\ufd50-\ufd8f\ufd92-\ufdc7\ufdf0-\ufdfb\ufe00-\ufe0f\ufe20-\ufe26\ufe33\ufe34\ufe4d-\ufe4f\ufe70-\ufe74\ufe76-\ufefc\uff10-\uff19\uff21-\uff3a\uff3f\uff41-\uff5a\uff66-\uffbe\uffc2-\uffc7\uffca-\uffcf\uffd2-\uffd7\uffda-\uffdc]"
    ),
})


def assert__py__(condition=None, message=None):
    if not condition:
        raise RuntimeError("ASSERT: " + message)


def isDecimalDigit(ch=None):
    return (ch >= 48) and (ch <= 57)


def isHexDigit(ch=None):
    return "0123456789abcdefABCDEF".find(ch) >= 0


def isOctalDigit(ch=None):
    return "01234567".find(ch) >= 0


def isWhiteSpace(ch=None):
    return (
        ((((ch == 32) or (ch == 9)) or (ch == 11)) or
         (ch == 12)) or (ch == 160)
    ) or ((ch >= 5760) and (
        u"\u1680\u180e\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u202f\u205f\u3000\ufeff"
        .find(unichr(ch)) > 0))


def isLineTerminator(ch=None):
    return (((ch == 10) or (ch == 13)) or (ch == 8232)) or (ch == 8233)


def isIdentifierStart(ch=None):
    return (((((ch == 36) or (ch == 95)) or ((ch >= 65) and (ch <= 90))) or
             ((ch >= 97) and (ch <= 122))) or
            (ch == 92)) or ((ch >= 128)
                            and Regex.NonAsciiIdentifierStart.test(unichr(ch)))


def isIdentifierPart(ch=None):
    return ((((((ch == 36) or (ch == 95)) or ((ch >= 65) and (ch <= 90))) or
              ((ch >= 97) and (ch <= 122))) or ((ch >= 48) and (ch <= 57))) or
            (ch == 92)) or ((ch >= 128)
                            and Regex.NonAsciiIdentifierPart.test(unichr(ch)))


def isFutureReservedWord(id=None):
    while 1:
        if (id == "super") or ((id == "import") or ((id == "extends") or
                                                    ((id == "export") or
                                                     ((id == "enum") or
                                                      (id == "class"))))):
            return True
        else:
            return False
        break


def isStrictModeReservedWord(id=None):
    while 1:
        if (id == "let") or ((id == "yield") or
                             ((id == "static") or
                              ((id == "public") or
                               ((id == "protected") or
                                ((id == "private") or
                                 ((id == "package") or
                                  ((id == "interface") or
                                   (id == "implements")))))))):
            return True
        else:
            return False
        break


def isRestrictedWord(id=None):
    return (id == "eval") or (id == "arguments")


def isKeyword(id=None):
    if strict and isStrictModeReservedWord(id):
        return True
    while 1:
        if len(id) == 2:
            return ((id == "if") or (id == "in")) or (id == "do")
        elif len(id) == 3:
            return ((((id == "var") or (id == "for")) or (id == "new")) or
                    (id == "try")) or (id == "let")
        elif len(id) == 4:
            return (((((id == "this") or (id == "else")) or (id == "case")) or
                     (id == "void")) or (id == "with")) or (id == "enum")
        elif len(id) == 5:
            return (((((((id == "while") or (id == "break")) or
                        (id == "catch")) or (id == "throw")) or
                      (id == "const")) or (id == "yield")) or
                    (id == "class")) or (id == "super")
        elif len(id) == 6:
            return (((((id == "return") or (id == "typeof")) or
                      (id == "delete")) or (id == "switch")) or
                    (id == "export")) or (id == "import")
        elif len(id) == 7:
            return ((id == "default") or
                    (id == "finally")) or (id == "extends")
        elif len(id) == 8:
            return ((id == "function") or
                    (id == "continue")) or (id == "debugger")
        elif len(id) == 10:
            return id == "instanceof"
        else:
            return False
        break


def addComment(type=None, value=None, start=None, end=None, loc=None):
    comment = None
    assert__py__(('undefined'
                  if not 'start' in locals() else typeof(start)) == "number",
                 "Comment must have valid position")
    if state.lastCommentStart >= start:
        return
    state.lastCommentStart = start
    comment = jsdict({
        "type": type,
        "value": value,
    })
    if extra.range:
        comment.range = [start, end]
    if extra.loc:
        comment.loc = loc
    extra.comments.append(comment)


def skipSingleLineComment():
    global index, lineNumber, lineStart
    start = None
    loc = None
    ch = None
    comment = None
    start = index - 2
    loc = jsdict({
        "start":
        jsdict({
            "line": lineNumber,
            "column": (index - lineStart) - 2,
        }),
    })
    while index < length:
        ch = (ord(source[index]) if index < len(source) else None)
        index += 1
        index
        if isLineTerminator(ch):
            if extra.comments:
                comment = source[(start + 2):(index - 1)]
                loc.end = jsdict({
                    "line": lineNumber,
                    "column": (index - lineStart) - 1,
                })
                addComment("Line", comment, start, index - 1, loc)
            if (ch == 13) and (
                (ord(source[index]) if index < len(source) else None) == 10):
                index += 1
                index
            lineNumber += 1
            lineNumber
            lineStart = index
            return
    if extra.comments:
        comment = source[(start + 2):index]
        loc.end = jsdict({
            "line": lineNumber,
            "column": index - lineStart,
        })
        addComment("Line", comment, start, index, loc)


def skipMultiLineComment():
    global index, lineNumber, lineStart
    start = None
    loc = None
    ch = None
    comment = None
    if extra.comments:
        start = index - 2
        loc = jsdict({
            "start":
            jsdict({
                "line": lineNumber,
                "column": (index - lineStart) - 2,
            }),
        })
    while index < length:
        ch = (ord(source[index]) if index < len(source) else None)
        if isLineTerminator(ch):
            if (ch == 13) and ((ord(source[index + 1]) if
                                (index + 1) < len(source) else None) == 10):
                index += 1
                index
            lineNumber += 1
            lineNumber
            index += 1
            index
            lineStart = index
            if index >= length:
                throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")
        elif ch == 42:
            if (ord(source[index + 1]) if
                (index + 1) < len(source) else None) == 47:
                index += 1
                index
                index += 1
                index
                if extra.comments:
                    comment = source[(start + 2):(index - 2)]
                    loc.end = jsdict({
                        "line": lineNumber,
                        "column": index - lineStart,
                    })
                    addComment("Block", comment, start, index, loc)
                return
            index += 1
            index
        else:
            index += 1
            index
    throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")


def skipComment():
    global index, lineNumber, lineStart
    ch = None
    while index < length:
        ch = (ord(source[index]) if index < len(source) else None)
        if isWhiteSpace(ch):
            index += 1
            index
        elif isLineTerminator(ch):
            index += 1
            index
            if (ch == 13) and (
                (ord(source[index]) if index < len(source) else None) == 10):
                index += 1
                index
            lineNumber += 1
            lineNumber
            lineStart = index
        elif ch == 47:
            ch = (ord(source[index + 1]) if
                  (index + 1) < len(source) else None)
            if ch == 47:
                index += 1
                index
                index += 1
                index
                skipSingleLineComment()
            elif ch == 42:
                index += 1
                index
                index += 1
                index
                skipMultiLineComment()
            else:
                break
        else:
            break


def scanHexEscape(prefix=None):
    global len__py__, index
    i = None
    len__py__ = None
    ch = None
    code = 0
    len__py__ = (4 if prefix == "u" else 2)
    i = 0
    while 1:
        if not (i < len__py__):
            break
        if (index < length) and isHexDigit(source[index]):
            index += 1
            ch = source[index - 1]
            code = (code * 16) + "0123456789abcdef".find(ch.lower())
        else:
            return ""
        i += 1
    return unichr(code)


def getEscapedIdentifier():
    global index
    ch = None
    id = None
    index += 1
    index += 1
    ch = (ord(source[index - 1]) if index - 1 < len(source) else None)
    id = unichr(ch)
    if ch == 92:
        if (ord(source[index]) if index < len(source) else None) != 117:
            throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")
        index += 1
        index
        ch = scanHexEscape("u")
        if ((not ch) or (ch == "\\")) or (not isIdentifierStart(
            (ord(ch[0]) if 0 < len(ch) else None))):
            throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")
        id = ch
    while index < length:
        ch = (ord(source[index]) if index < len(source) else None)
        if not isIdentifierPart(ch):
            break
        index += 1
        index
        id += unichr(ch)
        if ch == 92:
            id = id[0:(0 + (len(id) - 1))]
            if (ord(source[index]) if index < len(source) else None) != 117:
                throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")
            index += 1
            index
            ch = scanHexEscape("u")
            if ((not ch) or (ch == "\\")) or (not isIdentifierPart(
                (ord(ch[0]) if 0 < len(ch) else None))):
                throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")
            id += ch
    return id


def getIdentifier():
    global index
    start = None
    ch = None
    index += 1
    start = index - 1
    while index < length:
        ch = (ord(source[index]) if index < len(source) else None)
        if ch == 92:
            index = start
            return getEscapedIdentifier()
        if isIdentifierPart(ch):
            index += 1
            index
        else:
            break
    return source[start:index]


def scanIdentifier():
    start = None
    id = None
    type = None
    start = index
    id = (getEscapedIdentifier() if
          (ord(source[index]) if index < len(source) else None) == 92 else
          getIdentifier())
    if len(id) == 1:
        type = Token.Identifier
    elif isKeyword(id):
        type = Token.Keyword
    elif id == "null":
        type = Token.NullLiteral
    elif (id == "true") or (id == "false"):
        type = Token.BooleanLiteral
    else:
        type = Token.Identifier
    return jsdict({
        "type": type,
        "value": id,
        "lineNumber": lineNumber,
        "lineStart": lineStart,
        "range": [start, index],
    })


def scanPunctuator():
    global index
    start = index
    code = (ord(source[index]) if index < len(source) else None)
    code2 = None
    ch1 = source[index]
    ch2 = None
    ch3 = None
    ch4 = None
    while 1:
        if (code == 126) or ((code == 63) or ((code == 58) or
                                              ((code == 93) or
                                               ((code == 91) or
                                                ((code == 125) or
                                                 ((code == 123) or
                                                  ((code == 44) or
                                                   ((code == 59) or
                                                    ((code == 41) or
                                                     ((code == 40) or
                                                      (code == 46))))))))))):
            index += 1
            index
            if extra.tokenize:
                if code == 40:
                    extra.openParenToken = len(extra.tokens)
                elif code == 123:
                    extra.openCurlyToken = len(extra.tokens)
            return jsdict({
                "type": Token.Punctuator,
                "value": unichr(code),
                "lineNumber": lineNumber,
                "lineStart": lineStart,
                "range": [start, index],
            })
        else:
            code2 = (ord(source[index + 1]) if
                     (index + 1) < len(source) else None)
            if code2 == 61:
                while 1:
                    if (code == 124) or ((code == 94) or
                                         ((code == 62) or
                                          ((code == 60) or
                                           ((code == 47) or
                                            ((code == 45) or
                                             ((code == 43) or
                                              ((code == 42) or
                                               ((code == 38) or
                                                (code == 37))))))))):
                        index += 2
                        return jsdict({
                            "type": Token.Punctuator,
                            "value": unichr(code) + unichr(code2),
                            "lineNumber": lineNumber,
                            "lineStart": lineStart,
                            "range": [start, index],
                        })
                    elif (code == 61) or (code == 33):
                        index += 2
                        if (ord(source[index])
                                if index < len(source) else None) == 61:
                            index += 1
                            index
                        return jsdict({
                            "type": Token.Punctuator,
                            "value": source[start:index],
                            "lineNumber": lineNumber,
                            "lineStart": lineStart,
                            "range": [start, index],
                        })
                    else:
                        break
                    break
            break
        break
    ch2 = source[index + 1] if index + 1 < len(source) else None
    ch3 = source[index + 2] if index + 2 < len(source) else None
    ch4 = source[index + 3] if index + 3 < len(source) else None
    if ((ch1 == ">") and (ch2 == ">")) and (ch3 == ">"):
        if ch4 == "=":
            index += 4
            return jsdict({
                "type": Token.Punctuator,
                "value": ">>>=",
                "lineNumber": lineNumber,
                "lineStart": lineStart,
                "range": [start, index],
            })
    if ((ch1 == ">") and (ch2 == ">")) and (ch3 == ">"):
        index += 3
        return jsdict({
            "type": Token.Punctuator,
            "value": ">>>",
            "lineNumber": lineNumber,
            "lineStart": lineStart,
            "range": [start, index],
        })
    if ((ch1 == "<") and (ch2 == "<")) and (ch3 == "="):
        index += 3
        return jsdict({
            "type": Token.Punctuator,
            "value": "<<=",
            "lineNumber": lineNumber,
            "lineStart": lineStart,
            "range": [start, index],
        })
    if ((ch1 == ">") and (ch2 == ">")) and (ch3 == "="):
        index += 3
        return jsdict({
            "type": Token.Punctuator,
            "value": ">>=",
            "lineNumber": lineNumber,
            "lineStart": lineStart,
            "range": [start, index],
        })
    if (ch1 == ch2) and ("+-<>&|".find(ch1) >= 0):
        index += 2
        return jsdict({
            "type": Token.Punctuator,
            "value": ch1 + ch2,
            "lineNumber": lineNumber,
            "lineStart": lineStart,
            "range": [start, index],
        })
    if "<>=!+-*%&|^/".find(ch1) >= 0:
        index += 1
        index
        return jsdict({
            "type": Token.Punctuator,
            "value": ch1,
            "lineNumber": lineNumber,
            "lineStart": lineStart,
            "range": [start, index],
        })
    throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")


def scanHexLiteral(start=None):
    global index
    number = ""
    while index < length:
        if not isHexDigit(source[index]):
            break
        index += 1
        number += source[index - 1]
    if len(number) == 0:
        throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")
    if isIdentifierStart(
        (ord(source[index]) if index < len(source) else None)):
        throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")
    return jsdict({
        "type": Token.NumericLiteral,
        "value": parseInt("0x" + number, 16),
        "lineNumber": lineNumber,
        "lineStart": lineStart,
        "range": [start, index],
    })


def scanOctalLiteral(start=None):
    global index
    index += 1
    number = "0" + source[index - 1]
    while index < length:
        if not isOctalDigit(source[index]):
            break
        index += 1
        number += source[index - 1]
    if isIdentifierStart(
        (ord(source[index])
         if index < len(source) else None)) or isDecimalDigit(
             (ord(source[index]) if index < len(source) else None)):
        throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")
    return jsdict({
        "type": Token.NumericLiteral,
        "value": parseInt(number, 8),
        "octal": True,
        "lineNumber": lineNumber,
        "lineStart": lineStart,
        "range": [start, index],
    })


def scanNumericLiteral():
    global index
    number = None
    start = None
    ch = None
    ch = source[index]
    assert__py__(
        isDecimalDigit((ord(ch[0]) if 0 < len(ch) else None)) or (ch == "."),
        "Numeric literal must start with a decimal digit or a decimal point")
    start = index
    number = ""
    if ch != ".":
        index += 1
        number = source[index - 1]
        ch = source[index] if index < len(source) else None
        if number == "0":
            if (ch == "x") or (ch == "X"):
                index += 1
                index
                return scanHexLiteral(start)
            if isOctalDigit(ch):
                return scanOctalLiteral(start)
            if ch and isDecimalDigit((ord(ch[0]) if 0 < len(ch) else None)):
                throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")
        while isDecimalDigit(
            (ord(source[index]) if index < len(source) else None)):
            index += 1
            number += source[index - 1]
        ch = source[index] if index < len(source) else None
    if ch == ".":
        index += 1
        number += source[index - 1]
        while isDecimalDigit(
            (ord(source[index]) if index < len(source) else None)):
            index += 1
            number += source[index - 1]
        ch = source[index]
    if (ch == "e") or (ch == "E"):
        index += 1
        number += source[index - 1]
        ch = source[index]
        if (ch == "+") or (ch == "-"):
            index += 1
            number += source[index - 1]
        if isDecimalDigit(
            (ord(source[index]) if index < len(source) else None)):
            while isDecimalDigit(
                (ord(source[index]) if index < len(source) else None)):
                index += 1
                number += source[index - 1]
        else:
            throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")
    if isIdentifierStart(
        (ord(source[index]) if index < len(source) else None)):
        throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")
    return jsdict({
        "type": Token.NumericLiteral,
        "value": parseFloat(number),
        "lineNumber": lineNumber,
        "lineStart": lineStart,
        "range": [start, index],
    })


def scanStringLiteral():
    global index, lineNumber
    str = ""
    quote = None
    start = None
    ch = None
    code = None
    unescaped = None
    restore = None
    octal = False
    quote = source[index]
    assert__py__((quote == "'") or (quote == "\""),
                 "String literal must starts with a quote")
    start = index
    index += 1
    index
    while index < length:
        index += 1
        ch = source[index - 1]
        if ch == quote:
            quote = ""
            break
        elif ch == "\\":
            index += 1
            ch = source[index - 1]
            if (not ch) or (not isLineTerminator(
                (ord(ch[0]) if 0 < len(ch) else None))):
                while 1:
                    if ch == "n":
                        str += u"\x0a"
                        break
                    elif ch == "r":
                        str += u"\x0d"
                        break
                    elif ch == "t":
                        str += u"\x09"
                        break
                    elif (ch == "x") or (ch == "u"):
                        restore = index
                        unescaped = scanHexEscape(ch)
                        if unescaped:
                            str += unescaped
                        else:
                            index = restore
                            str += ch
                        break
                    elif ch == "b":
                        str += u"\x08"
                        break
                    elif ch == "f":
                        str += u"\x0c"
                        break
                    elif ch == "v":
                        str += u"\x0b"
                        break
                    else:
                        if isOctalDigit(ch):
                            code = "01234567".find(ch)
                            if code != 0:
                                octal = True
                            if (index < length) and isOctalDigit(
                                    source[index]):
                                octal = True
                                index += 1
                                code = (code * 8) + "01234567".find(
                                    source[index - 1])
                                if (("0123".find(ch) >= 0) and
                                    (index < length)) and isOctalDigit(
                                        source[index]):
                                    index += 1
                                    code = (code * 8) + "01234567".find(
                                        source[index - 1])
                            str += unichr(code)
                        else:
                            str += ch
                        break
                    break
            else:
                lineNumber += 1
                lineNumber
                if (ch == u"\x0d") and (source[index] == u"\x0a"):
                    index += 1
                    index
        elif isLineTerminator((ord(ch[0]) if 0 < len(ch) else None)):
            break
        else:
            str += ch
    if quote != "":
        throwError(jsdict({}), Messages.UnexpectedToken, "ILLEGAL")
    return jsdict({
        "type": Token.StringLiteral,
        "value": str,
        "octal": octal,
        "lineNumber": lineNumber,
        "lineStart": lineStart,
        "range": [start, index],
    })


def scanRegExp():
    global lookahead, index
    str = None
    ch = None
    start = None
    pattern = None
    flags = None
    value = None
    classMarker = False
    restore = None
    terminated = False
    lookahead = None
    skipComment()
    start = index
    ch = source[index]
    assert__py__(ch == "/",
                 "Regular expression literal must start with a slash")
    index += 1
    str = source[index - 1]
    while index < length:
        index += 1
        ch = source[index - 1]
        str += ch
        if classMarker:
            if ch == "]":
                classMarker = False
        else:
            if ch == "\\":
                index += 1
                ch = source[index - 1]
                if isLineTerminator((ord(ch[0]) if 0 < len(ch) else None)):
                    throwError(jsdict({}), Messages.UnterminatedRegExp)
                str += ch
            elif ch == "/":
                terminated = True
                break
            elif ch == "[":
                classMarker = True
            elif isLineTerminator((ord(ch[0]) if 0 < len(ch) else None)):
                throwError(jsdict({}), Messages.UnterminatedRegExp)
    if not terminated:
        throwError(jsdict({}), Messages.UnterminatedRegExp)
    pattern = str[1:(1 + (len(str) - 2))]
    flags = ""
    while index < length:
        ch = source[index]
        if not isIdentifierPart((ord(ch[0]) if 0 < len(ch) else None)):
            break
        index += 1
        index
        if (ch == "\\") and (index < length):
            ch = source[index]
            if ch == "u":
                index += 1
                index
                restore = index
                ch = scanHexEscape("u")
                if ch:
                    flags += ch
                    str += "\\u"
                    while 1:
                        if not (restore < index):
                            break
                        str += source[restore]
                        restore += 1
                else:
                    index = restore
                    flags += "u"
                    str += "\\u"
            else:
                str += "\\"
        else:
            flags += ch
            str += ch
    try:
        value = RegExp(pattern, flags)
    except Exception as e:
        throwError(jsdict({}), Messages.InvalidRegExp)
    peek()
    if extra.tokenize:
        return jsdict({
            "type": Token.RegularExpression,
            "value": value,
            "lineNumber": lineNumber,
            "lineStart": lineStart,
            "range": [start, index],
        })
    return jsdict({
        "literal": str,
        "value": value,
        "range": [start, index],
    })


def isIdentifierName(token=None):
    return (((token.type == Token.Identifier) or
             (token.type == Token.Keyword)) or
            (token.type == Token.BooleanLiteral)) or (
                token.type == Token.NullLiteral)


def advanceSlash():
    prevToken = None
    checkToken = None
    prevToken = extra.tokens[len(extra.tokens) - 1]
    if not prevToken:
        return scanRegExp()
    if prevToken.type == "Punctuator":
        if prevToken.value == ")":
            checkToken = extra.tokens[extra.openParenToken - 1]
            if (checkToken and (checkToken.type == "Keyword")) and (
                (((checkToken.value == "if") or
                  (checkToken.value == "while")) or
                 (checkToken.value == "for")) or (checkToken.value == "with")):
                return scanRegExp()
            return scanPunctuator()
        if prevToken.value == "}":
            if extra.tokens[extra.openCurlyToken - 3] and (
                    extra.tokens[extra.openCurlyToken - 3].type == "Keyword"):
                checkToken = extra.tokens[extra.openCurlyToken - 4]
                if not checkToken:
                    return scanPunctuator()
            elif extra.tokens[extra.openCurlyToken - 4] and (
                    extra.tokens[extra.openCurlyToken - 4].type == "Keyword"):
                checkToken = extra.tokens[extra.openCurlyToken - 5]
                if not checkToken:
                    return scanRegExp()
            else:
                return scanPunctuator()
            if FnExprTokens.indexOf(checkToken.value) >= 0:
                return scanPunctuator()
            return scanRegExp()
        return scanRegExp()
    if prevToken.type == "Keyword":
        return scanRegExp()
    return scanPunctuator()


def advance():
    ch = None
    skipComment()
    if index >= length:
        return jsdict({
            "type": Token.EOF,
            "lineNumber": lineNumber,
            "lineStart": lineStart,
            "range": [index, index],
        })
    ch = (ord(source[index]) if index < len(source) else None)
    if ((ch == 40) or (ch == 41)) or (ch == 58):
        return scanPunctuator()
    if (ch == 39) or (ch == 34):
        return scanStringLiteral()
    if isIdentifierStart(ch):
        return scanIdentifier()
    if ch == 46:
        if isDecimalDigit((ord(source[index + 1]) if
                           (index + 1) < len(source) else None)):
            return scanNumericLiteral()
        return scanPunctuator()
    if isDecimalDigit(ch):
        return scanNumericLiteral()
    if extra.tokenize and (ch == 47):
        return advanceSlash()
    return scanPunctuator()


def lex():
    global index, lineNumber, lineStart, lookahead
    token = None
    token = lookahead
    index = token.range[1]
    lineNumber = token.lineNumber
    lineStart = token.lineStart
    lookahead = advance()
    index = token.range[1]
    lineNumber = token.lineNumber
    lineStart = token.lineStart
    return token


def peek():
    global lookahead, index, lineNumber, lineStart
    pos = None
    line = None
    start = None
    pos = index
    line = lineNumber
    start = lineStart
    lookahead = advance()
    index = pos
    lineNumber = line
    lineStart = start


SyntaxTreeDelegate = jsdict({
    "name": "SyntaxTree",
    "markStart": __temp__0,
    "markEnd": __temp__1,
    "markEndIf": __temp__2,
    "postProcess": __temp__3,
    "createArrayExpression": __temp__4,
    "createAssignmentExpression": __temp__5,
    "createBinaryExpression": __temp__6,
    "createBlockStatement": __temp__7,
    "createBreakStatement": __temp__8,
    "createCallExpression": __temp__9,
    "createCatchClause": __temp__10,
    "createConditionalExpression": __temp__11,
    "createContinueStatement": __temp__12,
    "createDebuggerStatement": __temp__13,
    "createDoWhileStatement": __temp__14,
    "createEmptyStatement": __temp__15,
    "createExpressionStatement": __temp__16,
    "createForStatement": __temp__17,
    "createForInStatement": __temp__18,
    "createFunctionDeclaration": __temp__19,
    "createFunctionExpression": __temp__20,
    "createIdentifier": __temp__21,
    "createIfStatement": __temp__22,
    "createLabeledStatement": __temp__23,
    "createLiteral": __temp__24,
    "createMemberExpression": __temp__25,
    "createNewExpression": __temp__26,
    "createObjectExpression": __temp__27,
    "createPostfixExpression": __temp__28,
    "createProgram": __temp__29,
    "createProperty": __temp__30,
    "createReturnStatement": __temp__31,
    "createSequenceExpression": __temp__32,
    "createSwitchCase": __temp__33,
    "createSwitchStatement": __temp__34,
    "createThisExpression": __temp__35,
    "createThrowStatement": __temp__36,
    "createTryStatement": __temp__37,
    "createUnaryExpression": __temp__38,
    "createVariableDeclaration": __temp__39,
    "createVariableDeclarator": __temp__40,
    "createWhileStatement": __temp__41,
    "createWithStatement": __temp__42,
})


def peekLineTerminator():
    global index, lineNumber, lineStart
    pos = None
    line = None
    start = None
    found = None
    pos = index
    line = lineNumber
    start = lineStart
    skipComment()
    found = lineNumber != line
    index = pos
    lineNumber = line
    lineStart = start
    return found


def throwError(token=None, messageFormat=None, a=None):
    def __temp__43(whole=None, index=None):
        assert__py__(index < len(args), "Message reference must be in range")
        return args[index]

    error = None
    args = Array.prototype.slice.call(arguments, 2)
    msg = messageFormat.replace(RegExp(r'%(\d)'), __temp__43)
    if ('undefined' if not ('lineNumber' in token) else typeof(
            token.lineNumber)) == "number":
        error = RuntimeError((("Line " + token.lineNumber) + ": ") + msg)
        error.index = token.range[0]
        error.lineNumber = token.lineNumber
        error.column = (token.range[0] - lineStart) + 1
    else:
        error = RuntimeError((("Line " + lineNumber) + ": ") + msg)
        error.index = index
        error.lineNumber = lineNumber
        error.column = (index - lineStart) + 1
    error.description = msg
    raise error


def throwErrorTolerant():
    try:
        throwError.apply(None, arguments)
    except Exception as e:
        if extra.errors:
            extra.errors.append(e)
        else:
            raise


def throwUnexpected(token=None):
    if token.type == Token.EOF:
        throwError(token, Messages.UnexpectedEOS)
    if token.type == Token.NumericLiteral:
        throwError(token, Messages.UnexpectedNumber)
    if token.type == Token.StringLiteral:
        throwError(token, Messages.UnexpectedString)
    if token.type == Token.Identifier:
        throwError(token, Messages.UnexpectedIdentifier)
    if token.type == Token.Keyword:
        if isFutureReservedWord(token.value):
            throwError(token, Messages.UnexpectedReserved)
        elif strict and isStrictModeReservedWord(token.value):
            throwErrorTolerant(token, Messages.StrictReservedWord)
            return
        throwError(token, Messages.UnexpectedToken, token.value)
    throwError(token, Messages.UnexpectedToken, token.value)


def expect(value=None):
    token = lex()
    if (token.type != Token.Punctuator) or (token.value != value):
        throwUnexpected(token)


def expectKeyword(keyword=None):
    token = lex()
    if (token.type != Token.Keyword) or (token.value != keyword):
        throwUnexpected(token)


def match(value=None):
    return (lookahead.type == Token.Punctuator) and (lookahead.value == value)


def matchKeyword(keyword=None):
    return (lookahead.type == Token.Keyword) and (lookahead.value == keyword)


def matchAssign():
    op = None
    if lookahead.type != Token.Punctuator:
        return False
    op = lookahead.value
    return (((((((((((op == "=") or (op == "*=")) or (op == "/=")) or
                   (op == "%=")) or (op == "+=")) or (op == "-=")) or
                (op == "<<=")) or (op == ">>=")) or (op == ">>>=")) or
             (op == "&=")) or (op == "^=")) or (op == "|=")


def consumeSemicolon():
    line = None
    if (ord(source[index]) if index < len(source) else None) == 59:
        lex()
        return
    line = lineNumber
    skipComment()
    if lineNumber != line:
        return
    if match(";"):
        lex()
        return
    if (lookahead.type != Token.EOF) and (not match("}")):
        throwUnexpected(lookahead)


def isLeftHandSide(expr=None):
    return (expr.type == Syntax.Identifier) or (
        expr.type == Syntax.MemberExpression)


def parseArrayInitialiser():
    elements = []
    expect("[")
    while not match("]"):
        if match(","):
            lex()
            elements.append(None)
        else:
            elements.append(parseAssignmentExpression())
            if not match("]"):
                expect(",")
    expect("]")
    return delegate.createArrayExpression(elements)


def parsePropertyFunction(param=None, first=None):
    global strict
    previousStrict = None
    body = None
    previousStrict = strict
    skipComment()
    delegate.markStart()
    body = parseFunctionSourceElements()
    if (first and strict) and isRestrictedWord(param[0].name):
        throwErrorTolerant(first, Messages.StrictParamName)
    strict = previousStrict
    return delegate.markEnd(
        delegate.createFunctionExpression(None, param, [], body))


def parseObjectPropertyKey():
    token = None
    skipComment()
    delegate.markStart()
    token = lex()
    if (token.type == Token.StringLiteral) or (
            token.type == Token.NumericLiteral):
        if strict and token.octal:
            throwErrorTolerant(token, Messages.StrictOctalLiteral)
        return delegate.markEnd(delegate.createLiteral(token))
    return delegate.markEnd(delegate.createIdentifier(token.value))


def parseObjectProperty():
    token = None
    key = None
    id = None
    value = None
    param = None
    token = lookahead
    skipComment()
    delegate.markStart()
    if token.type == Token.Identifier:
        id = parseObjectPropertyKey()
        if (token.value == "get") and (not match(":")):
            key = parseObjectPropertyKey()
            expect("(")
            expect(")")
            value = parsePropertyFunction([])
            return delegate.markEnd(delegate.createProperty("get", key, value))
        if (token.value == "set") and (not match(":")):
            key = parseObjectPropertyKey()
            expect("(")
            token = lookahead
            if token.type != Token.Identifier:
                expect(")")
                throwErrorTolerant(token, Messages.UnexpectedToken,
                                   token.value)
                value = parsePropertyFunction([])
            else:
                param = [parseVariableIdentifier()]
                expect(")")
                value = parsePropertyFunction(param, token)
            return delegate.markEnd(delegate.createProperty("set", key, value))
        expect(":")
        value = parseAssignmentExpression()
        return delegate.markEnd(delegate.createProperty("init", id, value))
    if (token.type == Token.EOF) or (token.type == Token.Punctuator):
        throwUnexpected(token)
    else:
        key = parseObjectPropertyKey()
        expect(":")
        value = parseAssignmentExpression()
        return delegate.markEnd(delegate.createProperty("init", key, value))


def parseObjectInitialiser():
    properties = []
    property = None
    name = None
    key = None
    kind = None
    map = jsdict({})
    toString = str
    expect("{")
    while not match("}"):
        property = parseObjectProperty()
        if property.key.type == Syntax.Identifier:
            name = property.key.name
        else:
            name = toString(property.key.value)
        kind = (PropertyKind.Data if property.kind == "init" else (
            PropertyKind.Get if property.kind == "get" else PropertyKind.Set))
        key = "$" + name
        if key in map:
            if map[key] == PropertyKind.Data:
                if strict and (kind == PropertyKind.Data):
                    throwErrorTolerant(
                        jsdict({}), Messages.StrictDuplicateProperty)
                elif kind != PropertyKind.Data:
                    throwErrorTolerant(
                        jsdict({}), Messages.AccessorDataProperty)
            else:
                if kind == PropertyKind.Data:
                    throwErrorTolerant(
                        jsdict({}), Messages.AccessorDataProperty)
                elif map[key] & kind:
                    throwErrorTolerant(jsdict({}), Messages.AccessorGetSet)
            map[key] |= kind
        else:
            map[key] = kind
        properties.append(property)
        if not match("}"):
            expect(",")
    expect("}")
    return delegate.createObjectExpression(properties)


def parseGroupExpression():
    expr = None
    expect("(")
    expr = parseExpression()
    expect(")")
    return expr


def parsePrimaryExpression():
    type = None
    token = None
    expr = None
    if match("("):
        return parseGroupExpression()
    type = lookahead.type
    delegate.markStart()
    if type == Token.Identifier:
        expr = delegate.createIdentifier(lex().value)
    elif (type == Token.StringLiteral) or (type == Token.NumericLiteral):
        if strict and lookahead.octal:
            throwErrorTolerant(lookahead, Messages.StrictOctalLiteral)
        expr = delegate.createLiteral(lex())
    elif type == Token.Keyword:
        if matchKeyword("this"):
            lex()
            expr = delegate.createThisExpression()
        elif matchKeyword("function"):
            expr = parseFunctionExpression()
    elif type == Token.BooleanLiteral:
        token = lex()
        token.value = token.value == "true"
        expr = delegate.createLiteral(token)
    elif type == Token.NullLiteral:
        token = lex()
        token.value = None
        expr = delegate.createLiteral(token)
    elif match("["):
        expr = parseArrayInitialiser()
    elif match("{"):
        expr = parseObjectInitialiser()
    elif match("/") or match("/="):
        expr = delegate.createLiteral(scanRegExp())
    if expr:
        return delegate.markEnd(expr)
    throwUnexpected(lex())


def parseArguments():
    args = []
    expect("(")
    if not match(")"):
        while index < length:
            args.append(parseAssignmentExpression())
            if match(")"):
                break
            expect(",")
    expect(")")
    return args


def parseNonComputedProperty():
    token = None
    delegate.markStart()
    token = lex()
    if not isIdentifierName(token):
        throwUnexpected(token)
    return delegate.markEnd(delegate.createIdentifier(token.value))


def parseNonComputedMember():
    expect(".")
    return parseNonComputedProperty()


def parseComputedMember():
    expr = None
    expect("[")
    expr = parseExpression()
    expect("]")
    return expr


def parseNewExpression():
    callee = None
    args = None
    delegate.markStart()
    expectKeyword("new")
    callee = parseLeftHandSideExpression()
    args = (parseArguments() if match("(") else [])
    return delegate.markEnd(delegate.createNewExpression(callee, args))


def parseLeftHandSideExpressionAllowCall():
    marker = None
    expr = None
    args = None
    property = None
    marker = createLocationMarker()
    expr = (parseNewExpression()
            if matchKeyword("new") else parsePrimaryExpression())
    while (match(".") or match("[")) or match("("):
        if match("("):
            args = parseArguments()
            expr = delegate.createCallExpression(expr, args)
        elif match("["):
            property = parseComputedMember()
            expr = delegate.createMemberExpression("[", expr, property)
        else:
            property = parseNonComputedMember()
            expr = delegate.createMemberExpression(".", expr, property)
        if marker:
            marker.end()
            marker.apply(expr)
    return expr


def parseLeftHandSideExpression():
    marker = None
    expr = None
    property = None
    marker = createLocationMarker()
    expr = (parseNewExpression()
            if matchKeyword("new") else parsePrimaryExpression())
    while match(".") or match("["):
        if match("["):
            property = parseComputedMember()
            expr = delegate.createMemberExpression("[", expr, property)
        else:
            property = parseNonComputedMember()
            expr = delegate.createMemberExpression(".", expr, property)
        if marker:
            marker.end()
            marker.apply(expr)
    return expr


def parsePostfixExpression():
    expr = None
    token = None
    delegate.markStart()
    expr = parseLeftHandSideExpressionAllowCall()
    if lookahead.type == Token.Punctuator:
        if (match("++") or match("--")) and (not peekLineTerminator()):
            if (strict and
                (expr.type == Syntax.Identifier)) and isRestrictedWord(
                    expr.name):
                throwErrorTolerant(jsdict({}), Messages.StrictLHSPostfix)
            if not isLeftHandSide(expr):
                throwError(jsdict({}), Messages.InvalidLHSInAssignment)
            token = lex()
            expr = delegate.createPostfixExpression(token.value, expr)
    return delegate.markEndIf(expr)


def parseUnaryExpression():
    token = None
    expr = None
    delegate.markStart()
    if (lookahead.type != Token.Punctuator) and (lookahead.type !=
                                                 Token.Keyword):
        expr = parsePostfixExpression()
    elif match("++") or match("--"):
        token = lex()
        expr = parseUnaryExpression()
        if (strict and
            (expr.type == Syntax.Identifier)) and isRestrictedWord(expr.name):
            throwErrorTolerant(jsdict({}), Messages.StrictLHSPrefix)
        if not isLeftHandSide(expr):
            throwError(jsdict({}), Messages.InvalidLHSInAssignment)
        expr = delegate.createUnaryExpression(token.value, expr)
    elif ((match("+") or match("-")) or match("~")) or match("!"):
        token = lex()
        expr = parseUnaryExpression()
        expr = delegate.createUnaryExpression(token.value, expr)
    elif (matchKeyword("delete")
          or matchKeyword("void")) or matchKeyword("typeof"):
        token = lex()
        expr = parseUnaryExpression()
        expr = delegate.createUnaryExpression(token.value, expr)
        if (strict and (expr.operator == "delete")) and (
                expr.argument.type == Syntax.Identifier):
            throwErrorTolerant(jsdict({}), Messages.StrictDelete)
    else:
        expr = parsePostfixExpression()
    return delegate.markEndIf(expr)


def binaryPrecedence(token=None, allowIn=None):
    prec = 0
    if (token.type != Token.Punctuator) and (token.type != Token.Keyword):
        return 0
    while 1:
        if token.value == "||":
            prec = 1
            break
        elif token.value == "&&":
            prec = 2
            break
        elif token.value == "|":
            prec = 3
            break
        elif token.value == "^":
            prec = 4
            break
        elif token.value == "&":
            prec = 5
            break
        elif (token.value == "!==") or ((token.value == "===") or
                                        ((token.value == "!=") or
                                         (token.value == "=="))):
            prec = 6
            break
        elif (token.value == "instanceof") or ((token.value == ">=") or
                                               ((token.value == "<=") or
                                                ((token.value == ">") or
                                                 (token.value == "<")))):
            prec = 7
            break
        elif token.value == "in":
            prec = (7 if allowIn else 0)
            break
        elif (token.value == ">>>") or ((token.value == ">>") or
                                        (token.value == "<<")):
            prec = 8
            break
        elif (token.value == "-") or (token.value == "+"):
            prec = 9
            break
        elif (token.value == "%") or ((token.value == "/") or
                                      (token.value == "*")):
            prec = 11
            break
        else:
            break
        break
    return prec


def parseBinaryExpression():
    marker = None
    markers = None
    expr = None
    token = None
    prec = None
    previousAllowIn = None
    stack = None
    right = None
    operator = None
    left = None
    i = None
    previousAllowIn = state.allowIn
    state.allowIn = True
    marker = createLocationMarker()
    left = parseUnaryExpression()
    token = lookahead
    prec = binaryPrecedence(token, previousAllowIn)
    if prec == 0:
        return left
    token.prec = prec
    lex()
    markers = [marker, createLocationMarker()]
    right = parseUnaryExpression()
    stack = [left, token, right]
    prec = binaryPrecedence(lookahead, previousAllowIn)
    while prec > 0:
        while (len(stack) > 2) and (prec <= stack[len(stack) - 2].prec):
            right = stack.pop()
            operator = stack.pop().value
            left = stack.pop()
            expr = delegate.createBinaryExpression(operator, left, right)
            markers.pop()
            marker = markers.pop()
            if marker:
                marker.end()
                marker.apply(expr)
            stack.append(expr)
            markers.append(marker)
        token = lex()
        token.prec = prec
        stack.append(token)
        markers.append(createLocationMarker())
        expr = parseUnaryExpression()
        stack.append(expr)
        prec = binaryPrecedence(lookahead, previousAllowIn)
    state.allowIn = previousAllowIn
    i = len(stack) - 1
    expr = stack[i]
    markers.pop()
    while i > 1:
        expr = delegate.createBinaryExpression(stack[i - 1].value,
                                               stack[i - 2], expr)
        i -= 2
        marker = markers.pop()
        if marker:
            marker.end()
            marker.apply(expr)
    return expr


def parseConditionalExpression():
    expr = None
    previousAllowIn = None
    consequent = None
    alternate = None
    delegate.markStart()
    expr = parseBinaryExpression()
    if match("?"):
        lex()
        previousAllowIn = state.allowIn
        state.allowIn = True
        consequent = parseAssignmentExpression()
        state.allowIn = previousAllowIn
        expect(":")
        alternate = parseAssignmentExpression()
        expr = delegate.markEnd(
            delegate.createConditionalExpression(expr, consequent, alternate))
    else:
        delegate.markEnd(jsdict({}))
    return expr


def parseAssignmentExpression():
    token = None
    left = None
    right = None
    node = None
    token = lookahead
    delegate.markStart()
    left = parseConditionalExpression()
    node = left
    if matchAssign():
        if not isLeftHandSide(left):
            throwError(jsdict({}), Messages.InvalidLHSInAssignment)
        if (strict and
            (left.type == Syntax.Identifier)) and isRestrictedWord(left.name):
            throwErrorTolerant(token, Messages.StrictLHSAssignment)
        token = lex()
        right = parseAssignmentExpression()
        node = delegate.createAssignmentExpression(token.value, left, right)
    return delegate.markEndIf(node)


def parseExpression():
    expr = None
    delegate.markStart()
    expr = parseAssignmentExpression()
    if match(","):
        expr = delegate.createSequenceExpression([expr])
        while index < length:
            if not match(","):
                break
            lex()
            expr.expressions.append(parseAssignmentExpression())
    return delegate.markEndIf(expr)


def parseStatementList():
    list__py__ = []
    statement = None
    while index < length:
        if match("}"):
            break
        statement = parseSourceElement()
        if ('undefined' if not 'statement' in locals() else
                typeof(statement)) == "undefined":
            break
        list__py__.append(statement)
    return list__py__


def parseBlock():
    block = None
    skipComment()
    delegate.markStart()
    expect("{")
    block = parseStatementList()
    expect("}")
    return delegate.markEnd(delegate.createBlockStatement(block))


def parseVariableIdentifier():
    token = None
    skipComment()
    delegate.markStart()
    token = lex()
    if token.type != Token.Identifier:
        throwUnexpected(token)
    return delegate.markEnd(delegate.createIdentifier(token.value))


def parseVariableDeclaration(kind=None):
    init = None
    id = None
    skipComment()
    delegate.markStart()
    id = parseVariableIdentifier()
    if strict and isRestrictedWord(id.name):
        throwErrorTolerant(jsdict({}), Messages.StrictVarName)
    if kind == "const":
        expect("=")
        init = parseAssignmentExpression()
    elif match("="):
        lex()
        init = parseAssignmentExpression()
    return delegate.markEnd(delegate.createVariableDeclarator(id, init))


def parseVariableDeclarationList(kind=None):
    list__py__ = []
    while 1:
        list__py__.append(parseVariableDeclaration(kind))
        if not match(","):
            break
        lex()
        if not (index < length):
            break
    return list__py__


def parseVariableStatement():
    declarations = None
    expectKeyword("var")
    declarations = parseVariableDeclarationList()
    consumeSemicolon()
    return delegate.createVariableDeclaration(declarations, "var")


def parseConstLetDeclaration(kind=None):
    declarations = None
    skipComment()
    delegate.markStart()
    expectKeyword(kind)
    declarations = parseVariableDeclarationList(kind)
    consumeSemicolon()
    return delegate.markEnd(
        delegate.createVariableDeclaration(declarations, kind))


def parseEmptyStatement():
    expect(";")
    return delegate.createEmptyStatement()


def parseExpressionStatement():
    expr = parseExpression()
    consumeSemicolon()
    return delegate.createExpressionStatement(expr)


def parseIfStatement():
    test = None
    consequent = None
    alternate = None
    expectKeyword("if")
    expect("(")
    test = parseExpression()
    expect(")")
    consequent = parseStatement()
    if matchKeyword("else"):
        lex()
        alternate = parseStatement()
    else:
        alternate = None
    return delegate.createIfStatement(test, consequent, alternate)


def parseDoWhileStatement():
    body = None
    test = None
    oldInIteration = None
    expectKeyword("do")
    oldInIteration = state.inIteration
    state.inIteration = True
    body = parseStatement()
    state.inIteration = oldInIteration
    expectKeyword("while")
    expect("(")
    test = parseExpression()
    expect(")")
    if match(";"):
        lex()
    return delegate.createDoWhileStatement(body, test)


def parseWhileStatement():
    test = None
    body = None
    oldInIteration = None
    expectKeyword("while")
    expect("(")
    test = parseExpression()
    expect(")")
    oldInIteration = state.inIteration
    state.inIteration = True
    body = parseStatement()
    state.inIteration = oldInIteration
    return delegate.createWhileStatement(test, body)


def parseForVariableDeclaration():
    token = None
    declarations = None
    delegate.markStart()
    token = lex()
    declarations = parseVariableDeclarationList()
    return delegate.markEnd(
        delegate.createVariableDeclaration(declarations, token.value))


def parseForStatement():
    init = None
    test = None
    update = None
    left = None
    right = None
    body = None
    oldInIteration = None
    update = None
    test = update
    init = test
    expectKeyword("for")
    expect("(")
    if match(";"):
        lex()
    else:
        if matchKeyword("var") or matchKeyword("let"):
            state.allowIn = False
            init = parseForVariableDeclaration()
            state.allowIn = True
            if (len(init.declarations) == 1) and matchKeyword("in"):
                lex()
                left = init
                right = parseExpression()
                init = None
        else:
            state.allowIn = False
            init = parseExpression()
            state.allowIn = True
            if matchKeyword("in"):
                if not isLeftHandSide(init):
                    throwError(jsdict({}), Messages.InvalidLHSInForIn)
                lex()
                left = init
                right = parseExpression()
                init = None
        if ('undefined'
                if not 'left' in locals() else typeof(left)) == "undefined":
            expect(";")
    if ('undefined'
            if not 'left' in locals() else typeof(left)) == "undefined":
        if not match(";"):
            test = parseExpression()
        expect(";")
        if not match(")"):
            update = parseExpression()
    expect(")")
    oldInIteration = state.inIteration
    state.inIteration = True
    body = parseStatement()
    state.inIteration = oldInIteration
    return (delegate.createForStatement(init, test, update, body) if (
        'undefined' if not 'left' in locals() else typeof(left)) == "undefined"
            else delegate.createForInStatement(left, right, body))


def parseContinueStatement():
    label = None
    key = None
    expectKeyword("continue")
    if (ord(source[index]) if index < len(source) else None) == 59:
        lex()
        if not state.inIteration:
            throwError(jsdict({}), Messages.IllegalContinue)
        return delegate.createContinueStatement(None)
    if peekLineTerminator():
        if not state.inIteration:
            throwError(jsdict({}), Messages.IllegalContinue)
        return delegate.createContinueStatement(None)
    if lookahead.type == Token.Identifier:
        label = parseVariableIdentifier()
        key = "$" + label.name
        if not (key in state.labelSet):
            throwError(jsdict({}), Messages.UnknownLabel, label.name)
    consumeSemicolon()
    if (label == None) and (not state.inIteration):
        throwError(jsdict({}), Messages.IllegalContinue)
    return delegate.createContinueStatement(label)


def parseBreakStatement():
    label = None
    key = None
    expectKeyword("break")
    if (ord(source[index]) if index < len(source) else None) == 59:
        lex()
        if not (state.inIteration or state.inSwitch):
            throwError(jsdict({}), Messages.IllegalBreak)
        return delegate.createBreakStatement(None)
    if peekLineTerminator():
        if not (state.inIteration or state.inSwitch):
            throwError(jsdict({}), Messages.IllegalBreak)
        return delegate.createBreakStatement(None)
    if lookahead.type == Token.Identifier:
        label = parseVariableIdentifier()
        key = "$" + label.name
        if not (key in state.labelSet):
            throwError(jsdict({}), Messages.UnknownLabel, label.name)
    consumeSemicolon()
    if (label == None) and (not (state.inIteration or state.inSwitch)):
        throwError(jsdict({}), Messages.IllegalBreak)
    return delegate.createBreakStatement(label)


def parseReturnStatement():
    argument = None
    expectKeyword("return")
    if not state.inFunctionBody:
        throwErrorTolerant(jsdict({}), Messages.IllegalReturn)
    if (ord(source[index]) if index < len(source) else None) == 32:
        if isIdentifierStart((ord(source[index + 1]) if
                              (index + 1) < len(source) else None)):
            argument = parseExpression()
            consumeSemicolon()
            return delegate.createReturnStatement(argument)
    if peekLineTerminator():
        return delegate.createReturnStatement(None)
    if not match(";"):
        if (not match("}")) and (lookahead.type != Token.EOF):
            argument = parseExpression()
    consumeSemicolon()
    return delegate.createReturnStatement(argument)


def parseWithStatement():
    object = None
    body = None
    if strict:
        throwErrorTolerant(jsdict({}), Messages.StrictModeWith)
    expectKeyword("with")
    expect("(")
    object = parseExpression()
    expect(")")
    body = parseStatement()
    return delegate.createWithStatement(object, body)


def parseSwitchCase():
    test = None
    consequent = []
    statement = None
    skipComment()
    delegate.markStart()
    if matchKeyword("default"):
        lex()
        test = None
    else:
        expectKeyword("case")
        test = parseExpression()
    expect(":")
    while index < length:
        if (match("}") or matchKeyword("default")) or matchKeyword("case"):
            break
        statement = parseStatement()
        consequent.append(statement)
    return delegate.markEnd(delegate.createSwitchCase(test, consequent))


def parseSwitchStatement():
    discriminant = None
    cases = None
    clause = None
    oldInSwitch = None
    defaultFound = None
    expectKeyword("switch")
    expect("(")
    discriminant = parseExpression()
    expect(")")
    expect("{")
    if match("}"):
        lex()
        return delegate.createSwitchStatement(discriminant)
    cases = []
    oldInSwitch = state.inSwitch
    state.inSwitch = True
    defaultFound = False
    while index < length:
        if match("}"):
            break
        clause = parseSwitchCase()
        if clause.test == None:
            if defaultFound:
                throwError(jsdict({}), Messages.MultipleDefaultsInSwitch)
            defaultFound = True
        cases.append(clause)
    state.inSwitch = oldInSwitch
    expect("}")
    return delegate.createSwitchStatement(discriminant, cases)


def parseThrowStatement():
    argument = None
    expectKeyword("throw")
    if peekLineTerminator():
        throwError(jsdict({}), Messages.NewlineAfterThrow)
    argument = parseExpression()
    consumeSemicolon()
    return delegate.createThrowStatement(argument)


def parseCatchClause():
    param = None
    body = None
    skipComment()
    delegate.markStart()
    expectKeyword("catch")
    expect("(")
    if match(")"):
        throwUnexpected(lookahead)
    param = parseVariableIdentifier()
    if strict and isRestrictedWord(param.name):
        throwErrorTolerant(jsdict({}), Messages.StrictCatchVariable)
    expect(")")
    body = parseBlock()
    return delegate.markEnd(delegate.createCatchClause(param, body))


def parseTryStatement():
    block = None
    handlers = []
    finalizer = None
    expectKeyword("try")
    block = parseBlock()
    if matchKeyword("catch"):
        handlers.append(parseCatchClause())
    if matchKeyword("finally"):
        lex()
        finalizer = parseBlock()
    if (len(handlers) == 0) and (not finalizer):
        throwError(jsdict({}), Messages.NoCatchOrFinally)
    return delegate.createTryStatement(block, [], handlers, finalizer)


def parseDebuggerStatement():
    expectKeyword("debugger")
    consumeSemicolon()
    return delegate.createDebuggerStatement()


def parseStatement():
    type = lookahead.type
    expr = None
    labeledBody = None
    key = None
    if type == Token.EOF:
        throwUnexpected(lookahead)
    skipComment()
    delegate.markStart()
    if type == Token.Punctuator:
        while 1:
            if lookahead.value == ";":
                return delegate.markEnd(parseEmptyStatement())
            elif lookahead.value == "{":
                return delegate.markEnd(parseBlock())
            elif lookahead.value == "(":
                return delegate.markEnd(parseExpressionStatement())
            else:
                break
            break
    if type == Token.Keyword:
        while 1:
            if lookahead.value == "break":
                return delegate.markEnd(parseBreakStatement())
            elif lookahead.value == "continue":
                return delegate.markEnd(parseContinueStatement())
            elif lookahead.value == "debugger":
                return delegate.markEnd(parseDebuggerStatement())
            elif lookahead.value == "do":
                return delegate.markEnd(parseDoWhileStatement())
            elif lookahead.value == "for":
                return delegate.markEnd(parseForStatement())
            elif lookahead.value == "function":
                return delegate.markEnd(parseFunctionDeclaration())
            elif lookahead.value == "if":
                return delegate.markEnd(parseIfStatement())
            elif lookahead.value == "return":
                return delegate.markEnd(parseReturnStatement())
            elif lookahead.value == "switch":
                return delegate.markEnd(parseSwitchStatement())
            elif lookahead.value == "throw":
                return delegate.markEnd(parseThrowStatement())
            elif lookahead.value == "try":
                return delegate.markEnd(parseTryStatement())
            elif lookahead.value == "var":
                return delegate.markEnd(parseVariableStatement())
            elif lookahead.value == "while":
                return delegate.markEnd(parseWhileStatement())
            elif lookahead.value == "with":
                return delegate.markEnd(parseWithStatement())
            else:
                break
            break
    expr = parseExpression()
    if (expr.type == Syntax.Identifier) and match(":"):
        lex()
        key = "$" + expr.name
        if key in state.labelSet:
            throwError(jsdict({}), Messages.Redeclaration, "Label", expr.name)
        state.labelSet[key] = True
        labeledBody = parseStatement()
        del state.labelSet[key]
        return delegate.markEnd(
            delegate.createLabeledStatement(expr, labeledBody))
    consumeSemicolon()
    return delegate.markEnd(delegate.createExpressionStatement(expr))


def parseFunctionSourceElements():
    global strict
    sourceElement = None
    sourceElements = []
    token = None
    directive = None
    firstRestricted = None
    oldLabelSet = None
    oldInIteration = None
    oldInSwitch = None
    oldInFunctionBody = None
    skipComment()
    delegate.markStart()
    expect("{")
    while index < length:
        if lookahead.type != Token.StringLiteral:
            break
        token = lookahead
        sourceElement = parseSourceElement()
        sourceElements.append(sourceElement)
        if sourceElement.expression.type != Syntax.Literal:
            break
        directive = source[(token.range[0] + 1):(token.range[1] - 1)]
        if directive == "use strict":
            strict = True
            if firstRestricted:
                throwErrorTolerant(firstRestricted,
                                   Messages.StrictOctalLiteral)
        else:
            if (not firstRestricted) and token.octal:
                firstRestricted = token
    oldLabelSet = state.labelSet
    oldInIteration = state.inIteration
    oldInSwitch = state.inSwitch
    oldInFunctionBody = state.inFunctionBody
    state.labelSet = jsdict({})
    state.inIteration = False
    state.inSwitch = False
    state.inFunctionBody = True
    while index < length:
        if match("}"):
            break
        sourceElement = parseSourceElement()
        if ('undefined' if not 'sourceElement' in locals() else
                typeof(sourceElement)) == "undefined":
            break
        sourceElements.append(sourceElement)
    expect("}")
    state.labelSet = oldLabelSet
    state.inIteration = oldInIteration
    state.inSwitch = oldInSwitch
    state.inFunctionBody = oldInFunctionBody
    return delegate.markEnd(delegate.createBlockStatement(sourceElements))


def parseParams(firstRestricted=None):
    param = None
    params = []
    token = None
    stricted = None
    paramSet = None
    key = None
    message = None
    expect("(")
    if not match(")"):
        paramSet = jsdict({})
        while index < length:
            token = lookahead
            param = parseVariableIdentifier()
            key = "$" + token.value
            if strict:
                if isRestrictedWord(token.value):
                    stricted = token
                    message = Messages.StrictParamName
                if key in paramSet:
                    stricted = token
                    message = Messages.StrictParamDupe
            elif not firstRestricted:
                if isRestrictedWord(token.value):
                    firstRestricted = token
                    message = Messages.StrictParamName
                elif isStrictModeReservedWord(token.value):
                    firstRestricted = token
                    message = Messages.StrictReservedWord
                elif key in paramSet:
                    firstRestricted = token
                    message = Messages.StrictParamDupe
            params.append(param)
            paramSet[key] = True
            if match(")"):
                break
            expect(",")
    expect(")")
    return jsdict({
        "params": params,
        "stricted": stricted,
        "firstRestricted": firstRestricted,
        "message": message,
    })


def parseFunctionDeclaration():
    global strict
    id = None
    params = []
    body = None
    token = None
    stricted = None
    tmp = None
    firstRestricted = None
    message = None
    previousStrict = None
    skipComment()
    delegate.markStart()
    expectKeyword("function")
    token = lookahead
    id = parseVariableIdentifier()
    if strict:
        if isRestrictedWord(token.value):
            throwErrorTolerant(token, Messages.StrictFunctionName)
    else:
        if isRestrictedWord(token.value):
            firstRestricted = token
            message = Messages.StrictFunctionName
        elif isStrictModeReservedWord(token.value):
            firstRestricted = token
            message = Messages.StrictReservedWord
    tmp = parseParams(firstRestricted)
    params = tmp.params
    stricted = tmp.stricted
    firstRestricted = tmp.firstRestricted
    if tmp.message:
        message = tmp.message
    previousStrict = strict
    body = parseFunctionSourceElements()
    if strict and firstRestricted:
        throwError(firstRestricted, message)
    if strict and stricted:
        throwErrorTolerant(stricted, message)
    strict = previousStrict
    return delegate.markEnd(
        delegate.createFunctionDeclaration(id, params, [], body))


def parseFunctionExpression():
    global strict
    token = None
    id = None
    stricted = None
    firstRestricted = None
    message = None
    tmp = None
    params = []
    body = None
    previousStrict = None
    delegate.markStart()
    expectKeyword("function")
    if not match("("):
        token = lookahead
        id = parseVariableIdentifier()
        if strict:
            if isRestrictedWord(token.value):
                throwErrorTolerant(token, Messages.StrictFunctionName)
        else:
            if isRestrictedWord(token.value):
                firstRestricted = token
                message = Messages.StrictFunctionName
            elif isStrictModeReservedWord(token.value):
                firstRestricted = token
                message = Messages.StrictReservedWord
    tmp = parseParams(firstRestricted)
    params = tmp.params
    stricted = tmp.stricted
    firstRestricted = tmp.firstRestricted
    if tmp.message:
        message = tmp.message
    previousStrict = strict
    body = parseFunctionSourceElements()
    if strict and firstRestricted:
        throwError(firstRestricted, message)
    if strict and stricted:
        throwErrorTolerant(stricted, message)
    strict = previousStrict
    return delegate.markEnd(
        delegate.createFunctionExpression(id, params, [], body))


def parseSourceElement():
    if lookahead.type == Token.Keyword:
        while 1:
            if (lookahead.value == "let") or (lookahead.value == "const"):
                return parseConstLetDeclaration(lookahead.value)
            elif lookahead.value == "function":
                return parseFunctionDeclaration()
            else:
                return parseStatement()
            break
    if lookahead.type != Token.EOF:
        return parseStatement()


def parseSourceElements():
    global strict
    sourceElement = None
    sourceElements = []
    token = None
    directive = None
    firstRestricted = None
    while index < length:
        token = lookahead
        if token.type != Token.StringLiteral:
            break
        sourceElement = parseSourceElement()
        sourceElements.append(sourceElement)
        if sourceElement.expression.type != Syntax.Literal:
            break
        directive = source[(token.range[0] + 1):(token.range[1] - 1)]
        if directive == "use strict":
            strict = True
            if firstRestricted:
                throwErrorTolerant(firstRestricted,
                                   Messages.StrictOctalLiteral)
        else:
            if (not firstRestricted) and token.octal:
                firstRestricted = token
    while index < length:
        sourceElement = parseSourceElement()
        if ('undefined' if not 'sourceElement' in locals() else
                typeof(sourceElement)) == "undefined":
            break
        sourceElements.append(sourceElement)
    return sourceElements


def parseProgram():
    global strict
    body = None
    skipComment()
    delegate.markStart()
    strict = False
    peek()
    body = parseSourceElements()
    return delegate.markEnd(delegate.createProgram(body))


def collectToken():
    start = None
    loc = None
    token = None
    range = None
    value = None
    skipComment()
    start = index
    loc = jsdict({
        "start":
        jsdict({
            "line": lineNumber,
            "column": index - lineStart,
        }),
    })
    token = extra.advance()
    loc.end = jsdict({
        "line": lineNumber,
        "column": index - lineStart,
    })
    if token.type != Token.EOF:
        range = [token.range[0], token.range[1]]
        value = source[token.range[0]:token.range[1]]
        extra.tokens.append(
            jsdict({
                "type": TokenName[token.type],
                "value": value,
                "range": range,
                "loc": loc,
            }))
    return token


def collectRegex():
    pos = None
    loc = None
    regex = None
    token = None
    skipComment()
    pos = index
    loc = jsdict({
        "start":
        jsdict({
            "line": lineNumber,
            "column": index - lineStart,
        }),
    })
    regex = extra.scanRegExp()
    loc.end = jsdict({
        "line": lineNumber,
        "column": index - lineStart,
    })
    if not extra.tokenize:
        if len(extra.tokens) > 0:
            token = extra.tokens[len(extra.tokens) - 1]
            if (token.range[0] == pos) and (token.type == "Punctuator"):
                if (token.value == "/") or (token.value == "/="):
                    extra.tokens.pop()
        extra.tokens.append(
            jsdict({
                "type": "RegularExpression",
                "value": regex.literal,
                "range": [pos, index],
                "loc": loc,
            }))
    return regex


def filterTokenLocation():
    i = None
    entry = None
    token = None
    tokens = []
    i = 0
    while 1:
        if not (i < len(extra.tokens)):
            break
        entry = extra.tokens[i]
        token = jsdict({
            "type": entry.type,
            "value": entry.value,
        })
        if extra.range:
            token.range = entry.range
        if extra.loc:
            token.loc = entry.loc
        tokens.append(token)
        i += 1
    extra.tokens = tokens


class LocationMarker(object):
    def __init__(self=None):
        self.marker = [index, lineNumber, index - lineStart, 0, 0, 0]

    def end(self=None):
        self.marker[3] = index
        self.marker[4] = lineNumber
        self.marker[5] = index - lineStart

    def apply(self=None, node=None):
        if extra.range:
            node.range = [self.marker[0], self.marker[3]]
        if extra.loc:
            node.loc = jsdict({
                "start":
                jsdict({
                    "line": self.marker[1],
                    "column": self.marker[2],
                }),
                "end":
                jsdict({
                    "line": self.marker[4],
                    "column": self.marker[5],
                }),
            })
        node = delegate.postProcess(node)


def createLocationMarker():
    if (not extra.loc) and (not extra.range):
        return None
    skipComment()
    return LocationMarker()


def patch():
    global advance, scanRegExp
    if ('undefined' if not ('tokens' in extra) else typeof(
            extra.tokens)) != "undefined":
        extra.advance = advance
        extra.scanRegExp = scanRegExp
        advance = collectToken
        scanRegExp = collectRegex


def unpatch():
    global advance, scanRegExp
    if ('undefined' if not ('scanRegExp' in extra) else typeof(
            extra.scanRegExp)) == "function":
        advance = extra.advance
        scanRegExp = extra.scanRegExp


def tokenize(code, **options):
    global delegate, source, index, lineNumber, lineStart, length, lookahead, state, extra
    options = jsdict(options)
    toString = None
    token = None
    tokens = None
    toString = str
    if (('undefined' if not 'code' in locals() else typeof(code)) !=
            "string") and (not isinstance(code, str)):
        code = toString(code)
    delegate = SyntaxTreeDelegate
    source = code
    index = 0
    lineNumber = (1 if len(source) > 0 else 0)
    lineStart = 0
    length = len(source)
    lookahead = None
    state = jsdict({
        "allowIn": True,
        "labelSet": jsdict({}),
        "inFunctionBody": False,
        "inIteration": False,
        "inSwitch": False,
        "lastCommentStart": -1,
    })
    extra = jsdict({})
    options = options or jsdict({})
    options.tokens = True
    extra.tokens = []
    extra.tokenize = True
    extra.openParenToken = -1
    extra.openCurlyToken = -1
    extra.range = (('undefined' if not ('range' in options) else typeof(
        options.range)) == "boolean") and options.range
    extra.loc = (('undefined' if not ('loc' in options) else typeof(
        options.loc)) == "boolean") and options.loc
    if (('undefined' if not ('comment' in options) else typeof(
            options.comment)) == "boolean") and options.comment:
        extra.comments = []
    if (('undefined' if not ('tolerant' in options) else typeof(
            options.tolerant)) == "boolean") and options.tolerant:
        extra.errors = []
    if length > 0:
        if (typeof(source[0])) == "undefined":
            if isinstance(code, str):
                source = code.valueOf()
    patch()
    try:
        peek()
        if lookahead.type == Token.EOF:
            return extra.tokens
        token = lex()
        while lookahead.type != Token.EOF:
            try:
                token = lex()
            except Exception as lexError:
                token = lookahead
                if extra.errors:
                    extra.errors.append(lexError)
                    break
                else:
                    raise
        filterTokenLocation()
        tokens = extra.tokens
        if ('undefined' if not ('comments' in extra) else typeof(
                extra.comments)) != "undefined":
            tokens.comments = extra.comments
        if ('undefined' if not ('errors' in extra) else typeof(
                extra.errors)) != "undefined":
            tokens.errors = extra.errors
    except Exception as e:
        raise
    finally:
        unpatch()
        extra = jsdict({})
    return tokens


def parse(code, **options):
    global delegate, source, index, lineNumber, lineStart, length, lookahead, state, extra
    options = jsdict(options)
    program = None
    toString = None
    toString = str
    if (('undefined' if not 'code' in locals() else typeof(code)) !=
            "string") and (not isinstance(code, str)):
        code = toString(code)
    delegate = SyntaxTreeDelegate
    source = code
    index = 0
    lineNumber = (1 if len(source) > 0 else 0)
    lineStart = 0
    length = len(source)
    lookahead = None
    state = jsdict({
        "allowIn": True,
        "labelSet": jsdict({}),
        "inFunctionBody": False,
        "inIteration": False,
        "inSwitch": False,
        "lastCommentStart": -1,
        "markerStack": [],
    })
    extra = jsdict({})
    if ('undefined'
            if not 'options' in locals() else typeof(options)) != "undefined":
        extra.range = (('undefined' if not ('range' in options) else typeof(
            options.range)) == "boolean") and options.range
        extra.loc = (('undefined' if not ('loc' in options) else typeof(
            options.loc)) == "boolean") and options.loc
        if (extra.loc and
            (options.source != None)) and (options.source != undefined):
            extra.source = toString(options.source)
        if (('undefined' if not ('tokens' in options) else typeof(
                options.tokens)) == "boolean") and options.tokens:
            extra.tokens = []
        if (('undefined' if not ('comment' in options) else typeof(
                options.comment)) == "boolean") and options.comment:
            extra.comments = []
        if (('undefined' if not ('tolerant' in options) else typeof(
                options.tolerant)) == "boolean") and options.tolerant:
            extra.errors = []
    if length > 0:
        if (typeof(source[0])) == "undefined":
            if isinstance(code, str):
                source = code.valueOf()
    patch()
    try:
        program = parseProgram()
        if ('undefined' if not ('comments' in extra) else typeof(
                extra.comments)) != "undefined":
            program.comments = extra.comments
        if ('undefined' if not ('tokens' in extra) else typeof(
                extra.tokens)) != "undefined":
            filterTokenLocation()
            program.tokens = extra.tokens
        if ('undefined' if not ('errors' in extra) else typeof(
                extra.errors)) != "undefined":
            program.errors = extra.errors
    except Exception as e:
        raise
    finally:
        unpatch()
        extra = jsdict({})
    return program


parse('var = 490 \n a=4;')
