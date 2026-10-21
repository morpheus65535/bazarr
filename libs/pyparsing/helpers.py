# helpers.py
from enum import Enum, auto
import html.entities
import operator
import re
import sys
import typing

from . import __diag__
from .core import *
from .util import (
    _bslash,
    _flatten,
    _escape_regex_range_chars,
    make_compressed_re,
    replaced_by_pep8,
)


def _suppression(expr: Union[ParserElement, str]) -> ParserElement:
    # internal helper to avoid wrapping Suppress inside another Suppress
    if isinstance(expr, Suppress):
        return expr
    return Suppress(expr)


#
# global helpers
#
def counted_array(
    expr: ParserElement, int_expr: typing.Optional[ParserElement] = None, **kwargs
) -> ParserElement:
    """Helper to define a counted list of expressions.

    This helper defines a pattern of the form::

        integer expr expr expr...

    where the leading integer tells how many expr expressions follow.
    The matched tokens returns the array of expr tokens as a list - the
    leading count token is suppressed.

    If ``int_expr`` is specified, it should be a pyparsing expression
    that produces an integer value.

    Examples:

    .. doctest::

        >>> counted_array(Word(alphas)).parse_string('2 ab cd ef')
        ParseResults(['ab', 'cd'], {})

    - In this parser, the leading integer value is given in binary,
      '10' indicating that 2 values are in the array:

      .. doctest::

        >>> binary_constant = Word('01').set_parse_action(lambda t: int(t[0], 2))
        >>> counted_array(Word(alphas), int_expr=binary_constant
        ...     ).parse_string('10 ab cd ef')
        ParseResults(['ab', 'cd'], {})

    - If other fields must be parsed after the count but before the
      list items, give the fields results names and they will
      be preserved in the returned ParseResults:

      .. doctest::

         >>> ppc = pyparsing.common
         >>> count_with_metadata = ppc.integer + Word(alphas)("type")
         >>> typed_array = counted_array(Word(alphanums),
         ...     int_expr=count_with_metadata)("items")
         >>> result = typed_array.parse_string("3 bool True True False")
         >>> print(result.dump())
         ['True', 'True', 'False']
         - items: ['True', 'True', 'False']
         - type: 'bool'
    """
    intExpr: typing.Optional[ParserElement] = deprecate_argument(
        kwargs, "intExpr", None
    )

    intExpr = intExpr or int_expr
    array_expr = Forward()

    def count_field_parse_action(s, l, t):
        nonlocal array_expr
        n = t[0]
        array_expr <<= (expr * n) if n else Empty()
        # clear list contents, but keep any named results
        del t[:]

    if intExpr is None:
        intExpr = Word(nums).set_parse_action(lambda t: int(t[0]))
    else:
        intExpr = intExpr.copy()
    intExpr.set_name("arrayLen")
    intExpr.add_parse_action(count_field_parse_action, call_during_try=True)
    return (intExpr + array_expr).set_name(f"(len) {expr}...")


def match_previous_literal(expr: ParserElement) -> ParserElement:
    """Helper to define an expression that is indirectly defined from
    the tokens matched in a previous expression, that is, it looks for
    a 'repeat' of a previous expression.  For example::

    .. testcode::

       first = Word(nums)
       second = match_previous_literal(first)
       match_expr = first + ":" + second

    will match ``"1:1"``, but not ``"1:2"``.  Because this
    matches a previous literal, will also match the leading
    ``"1:1"`` in ``"1:10"``. If this is not desired, use
    :class:`match_previous_expr`. Do *not* use with packrat parsing
    enabled.
    """
    rep = Forward()

    def copy_token_to_repeater(s, l, t):
        if not t:
            rep << Empty()
            return

        if len(t) == 1:
            rep << t[0]
            return

        # flatten t tokens
        tflat = _flatten(t.as_list())
        rep << And(Literal(tt) for tt in tflat)

    expr.add_parse_action(copy_token_to_repeater, call_during_try=True)
    rep.set_name(f"(prev) {expr}")
    return rep


def match_previous_expr(expr: ParserElement) -> ParserElement:
    """Helper to define an expression that is indirectly defined from
    the tokens matched in a previous expression, that is, it looks for
    a 'repeat' of a previous expression.  For example:

    .. testcode::

       first = Word(nums)
       second = match_previous_expr(first)
       match_expr = first + ":" + second

    will match ``"1:1"``, but not ``"1:2"``.  Because this
    matches by expressions, will *not* match the leading ``"1:1"``
    in ``"1:10"``; the expressions are evaluated first, and then
    compared, so ``"1"`` is compared with ``"10"``. Do *not* use
    with packrat parsing enabled.
    """
    rep = Forward()
    e2 = expr.copy()
    rep <<= e2

    def copy_token_to_repeater(s, l, t):
        matchTokens = _flatten(t.as_list())

        def must_match_these_tokens(s, l, t):
            theseTokens = _flatten(t.as_list())
            if theseTokens != matchTokens:
                raise ParseException(
                    s, l, f"Expected {matchTokens}, found{theseTokens}"
                )

        rep.set_parse_action(must_match_these_tokens, call_during_try=True)

    expr.add_parse_action(copy_token_to_repeater, call_during_try=True)
    rep.set_name(f"(prev) {expr}")
    return rep


def one_of(
    strs: Union[typing.Iterable[str], str],
    caseless: bool = False,
    use_regex: bool = True,
    as_keyword: bool = False,
    **kwargs,
) -> ParserElement:
    """Helper to quickly define a set of alternative :class:`Literal` s,
    and makes sure to do longest-first testing when there is a conflict,
    regardless of the input order, but returns
    a :class:`MatchFirst` for best performance.

    :param strs: a string of space-delimited literals, or a collection of
       string literals
    :param caseless: treat all literals as caseless
    :param use_regex: bool - as an optimization, will
       generate a :class:`Regex` object; otherwise, will generate
       a :class:`MatchFirst` object (if ``caseless=True`` or
       ``as_keyword=True``, or if creating a :class:`Regex` raises an exception)
    :param as_keyword: bool - enforce :class:`Keyword`-style matching on the
       generated expressions

    Parameters ``asKeyword`` and ``useRegex`` are retained for pre-PEP8
    compatibility, but will be removed in a future release.

    Example:

    .. testcode::

       comp_oper = one_of("< = > <= >= !=")
       var = Word(alphas)
       number = Word(nums)
       term = var | number
       comparison_expr = term + comp_oper + term
       print(comparison_expr.search_string("B = 12  AA=23 B<=AA AA>12"))

    prints:

    .. testoutput::

       [['B', '=', '12'], ['AA', '=', '23'], ['B', '<=', 'AA'], ['AA', '>', '12']]
    """
    useRegex: bool = deprecate_argument(kwargs, "useRegex", True)
    asKeyword: bool = deprecate_argument(kwargs, "asKeyword", False)

    asKeyword = asKeyword or as_keyword
    useRegex = useRegex and use_regex

    if (
        isinstance(caseless, str_type)
        and __diag__.warn_on_multiple_string_args_to_oneof
    ):
        warnings.warn(
            "warn_on_multiple_string_args_to_oneof:"
            " More than one string argument passed to one_of, pass"
            " choices as a list or space-delimited string",
            PyparsingDiagnosticWarning,
            stacklevel=2,
        )

    if caseless:
        is_equal = lambda a, b: a.upper() == b.upper()
        masks = lambda a, b: b.upper().startswith(a.upper())
    else:
        is_equal = operator.eq
        masks = lambda a, b: b.startswith(a)

    symbols: list[str]
    if isinstance(strs, str_type):
        strs = typing.cast(str, strs)
        symbols = strs.split()
    elif isinstance(strs, Iterable):
        symbols = list(strs)
    else:
        raise TypeError("Invalid argument to one_of, expected string or iterable")
    if not symbols:
        return NoMatch()

    # reorder given symbols to take care to avoid masking longer choices with shorter ones
    # (but only if the given symbols are not just single characters)
    i = 0
    while i < len(symbols) - 1:
        cur = symbols[i]
        for j, other in enumerate(symbols[i + 1 :]):
            if is_equal(other, cur):
                del symbols[i + j + 1]
                break
            if len(other) > len(cur) and masks(cur, other):
                del symbols[i + j + 1]
                symbols.insert(i, other)
                break
        else:
            i += 1

    if useRegex:
        re_flags: int = re.IGNORECASE if caseless else 0

        try:
            if all(len(sym) == 1 for sym in symbols):
                # symbols are just single characters, create range regex pattern
                patt = f"[{''.join(_escape_regex_range_chars(sym) for sym in symbols)}]"
            else:
                patt = "|".join(re.escape(sym) for sym in symbols)

            # wrap with \b word break markers if defining as keywords
            if asKeyword:
                patt = rf"\b(?:{patt})\b"

            ret = Regex(patt, flags=re_flags)
            ret.set_name(" | ".join(repr(s) for s in symbols))

            if caseless:
                # add parse action to return symbols as specified, not in random
                # casing as found in input string
                symbol_map = {sym.lower(): sym for sym in symbols}
                ret.add_parse_action(lambda s, l, t: symbol_map[t[0].lower()])

            return ret

        except re.error:
            warnings.warn(
                "Exception creating Regex for one_of, building MatchFirst",
                PyparsingDiagnosticWarning,
                stacklevel=2,
            )

    # last resort, just use MatchFirst of Token class corresponding to caseless
    # and asKeyword settings
    CASELESS = KEYWORD = True
    parse_element_class = {
        (CASELESS, KEYWORD): CaselessKeyword,
        (CASELESS, not KEYWORD): CaselessLiteral,
        (not CASELESS, KEYWORD): Keyword,
        (not CASELESS, not KEYWORD): Literal,
    }[(caseless, asKeyword)]
    return MatchFirst(parse_element_class(sym) for sym in symbols).set_name(
        " | ".join(symbols)
    )


def dict_of(key: ParserElement, value: ParserElement) -> Dict:
    """Helper to easily and clearly define a dictionary by specifying
    the respective patterns for the key and value.  Takes care of
    defining the :class:`Dict`, :class:`ZeroOrMore`, and
    :class:`Group` tokens in the proper order.  The key pattern
    can include delimiting markers or punctuation, as long as they are
    suppressed, thereby leaving the significant key text.  The value
    pattern can include named results, so that the :class:`Dict` results
    can include named token fields.

    Example:

    .. doctest::

       >>> text = "shape: SQUARE posn: upper left color: light blue texture: burlap"

       >>> data_word = Word(alphas)
       >>> label = data_word + FollowedBy(':')
       >>> attr_expr = (
       ...    label
       ...    + Suppress(':')
       ...    + OneOrMore(data_word, stop_on=label)
       ...    .set_parse_action(' '.join))
       >>> print(attr_expr[1, ...].parse_string(text).dump())
       ['shape', 'SQUARE', 'posn', 'upper left', 'color', 'light blue', 'texture', 'burlap']

       >>> attr_label = label
       >>> attr_value = Suppress(':') + OneOrMore(data_word, stop_on=label
       ...   ).set_parse_action(' '.join)

       # similar to Dict, but simpler call format
       >>> result = dict_of(attr_label, attr_value).parse_string(text)
       >>> print(result.dump())
       [['shape', 'SQUARE'], ['posn', 'upper left'], ['color', 'light blue'], ['texture', 'burlap']]
       - color: 'light blue'
       - posn: 'upper left'
       - shape: 'SQUARE'
       - texture: 'burlap'
       [0]:
         ['shape', 'SQUARE']
       [1]:
         ['posn', 'upper left']
       [2]:
         ['color', 'light blue']
       [3]:
         ['texture', 'burlap']

       >>> print(result['shape'])
       SQUARE
       >>> print(result.shape)  # object attribute access works too
       SQUARE
       >>> print(result.as_dict())
       {'shape': 'SQUARE', 'posn': 'upper left', 'color': 'light blue', 'texture': 'burlap'}
    """
    return Dict(OneOrMore(Group(key + value)))


def original_text_for(
    expr: ParserElement, as_string: bool = True, **kwargs
) -> ParserElement:
    """Helper to return the original, untokenized text for a given
    expression.  Useful to restore the parsed fields of an HTML start
    tag into the raw tag text itself, or to revert separate tokens with
    intervening whitespace back to the original matching input text. By
    default, returns a string containing the original parsed text.

    If the optional ``as_string`` argument is passed as
    ``False``, then the return value is
    a :class:`ParseResults` containing any results names that
    were originally matched, and a single token containing the original
    matched text from the input string.  So if the expression passed to
    :class:`original_text_for` contains expressions with defined
    results names, you must set ``as_string`` to ``False`` if you
    want to preserve those results name values.

    The ``asString`` pre-PEP8 argument is retained for compatibility,
    but will be removed in a future release.

    Example:

    .. testcode::

       src = "this is test <b> bold <i>text</i> </b> normal text "
       for tag in ("b", "i"):
           opener, closer = make_html_tags(tag)
           patt = original_text_for(opener + ... + closer)
           print(patt.search_string(src)[0])

    prints:

    .. testoutput::

       ['<b> bold <i>text</i> </b>']
       ['<i>text</i>']
    """
    asString: bool = deprecate_argument(kwargs, "asString", True)

    asString = asString and as_string

    locMarker = Empty().set_parse_action(lambda s, loc, t: loc)
    endlocMarker = locMarker.copy()
    endlocMarker.callPreparse = False
    matchExpr = locMarker("_original_start") + expr + endlocMarker("_original_end")
    if asString:
        extractText = lambda s, l, t: s[t._original_start : t._original_end]
    else:

        def extractText(s, l, t):
            t[:] = [s[t.pop("_original_start") : t.pop("_original_end")]]

    matchExpr.set_parse_action(extractText)
    matchExpr.ignoreExprs = expr.ignoreExprs
    matchExpr.suppress_warning(Diagnostics.warn_ungrouped_named_tokens_in_collection)
    return matchExpr


def ungroup(expr: ParserElement) -> ParserElement:
    """Helper to undo pyparsing's default grouping of And expressions,
    even if all but one are non-empty.
    """
    return TokenConverter(expr).add_parse_action(lambda t: t[0])


def locatedExpr(expr: ParserElement) -> ParserElement:
    """
    .. deprecated:: 3.0.0
       Use the :class:`Located` class instead. Note that `Located`
       returns results with one less grouping level.

    Helper to decorate a returned token with its starting and ending
    locations in the input string.

    This helper adds the following results names:

    - ``locn_start`` - location where matched expression begins
    - ``locn_end`` - location where matched expression ends
    - ``value`` - the actual parsed results

    Be careful if the input text contains ``<TAB>`` characters, you
    may want to call :meth:`ParserElement.parse_with_tabs`
    """
    warnings.warn(
        f"{'locatedExpr'!r} deprecated - use {'Located'!r}",
        PyparsingDeprecationWarning,
        stacklevel=2,
    )

    locator = Empty().set_parse_action(lambda ss, ll, tt: ll)
    return Group(
        locator("locn_start")
        + expr("value")
        + locator.copy().leave_whitespace()("locn_end")
    )


# define special default value to permit None as a significant value for
# ignore_expr
_NO_IGNORE_EXPR_GIVEN = NoMatch()


class _NestedExpr(ParseElementEnhance):
    """Helper method for defining nested lists enclosed in opening and
    closing delimiters (``"("`` and ``")"`` are the default).

    :param opener: str - opening character for a nested list
       (default= ``"("``); can also be a pyparsing expression

    :param closer: str - closing character for a nested list
       (default= ``")"``); can also be a pyparsing expression

    :param content: expression for items within the nested lists

    :param ignore_expr: expression for ignoring opening and closing delimiters
       (default = :class:`quoted_string`)

    Parameter ``ignoreExpr`` is retained for compatibility
    but will be removed in a future release.

    If an expression is not provided for the content argument, the
    nested expression will capture all whitespace-delimited content
    between delimiters as a list of separate values.

    Use the ``ignore_expr`` argument to define expressions that may
    contain opening or closing characters that should not be treated as
    opening or closing characters for nesting, such as quoted_string or
    a comment expression.  Specify multiple expressions using an
    :class:`Or` or :class:`MatchFirst`. The default is
    :class:`quoted_string`, but if no expressions are to be ignored, then
    pass ``None`` for this argument.

    Example:

    .. testcode::

       data_type = one_of("void int short long char float double")
       decl_data_type = Combine(data_type + Opt(Word('*')))
       ident = Word(alphas+'_', alphanums+'_')
       number = pyparsing_common.number
       arg = Group(decl_data_type + ident)
       LPAR, RPAR = map(Suppress, "()")

       code_body = nested_expr('{', '}', ignore_expr=(quoted_string | c_style_comment))

       c_function = (decl_data_type("type")
                     + ident("name")
                     + LPAR + Opt(DelimitedList(arg), [])("args") + RPAR
                     + code_body("body"))
       c_function.ignore(c_style_comment)

       source_code = '''
           int is_odd(int x) {
               return (x%2);
           }

           int dec_to_hex(char hchar) {
               if (hchar >= '0' && hchar <= '9') {
                   return (ord(hchar)-ord('0'));
               } else {
                   return (10+ord(hchar)-ord('A'));
               }
           }
       '''
       for func in c_function.search_string(source_code):
           print(f"{func.name} ({func.type}) args: {func.args}")


    prints:

    .. testoutput::

       is_odd (int) args: [['int', 'x']]
       dec_to_hex (int) args: [['char', 'hchar']]
    """

    def __init__(
        self,
        opener: Union[str, ParserElement] = "(",
        closer: Union[str, ParserElement] = ")",
        content: typing.Optional[ParserElement] = None,
        ignore_expr: typing.Optional[ParserElement] = _NO_IGNORE_EXPR_GIVEN,
        **kwargs,
    ):
        ignoreExpr = deprecate_argument(kwargs, "ignoreExpr", _NO_IGNORE_EXPR_GIVEN)
        if ignoreExpr != ignore_expr:
            ignoreExpr = (
                ignore_expr if ignoreExpr is _NO_IGNORE_EXPR_GIVEN else ignoreExpr
            )
        if ignoreExpr is _NO_IGNORE_EXPR_GIVEN:
            ignoreExpr = quoted_string()

        if opener == closer:
            raise ValueError("opening and closing strings cannot be the same")

        original_content = content
        if content is None:
            if isinstance(opener, str_type) and isinstance(closer, str_type):
                opener_str = str(opener)
                closer_str = str(closer)
                if len(opener_str) == 1 and len(closer_str) == 1:
                    if ignoreExpr is not None:
                        content = Combine(
                            OneOrMore(
                                ~ignoreExpr
                                + CharsNotIn(
                                    opener_str
                                    + closer_str
                                    + ParserElement.DEFAULT_WHITE_CHARS,
                                    exact=1,
                                )
                            )
                        )
                    else:
                        content = Combine(
                            Empty()
                            + CharsNotIn(
                                opener_str
                                + closer_str
                                + ParserElement.DEFAULT_WHITE_CHARS
                            )
                        )
                else:
                    if ignoreExpr is not None:
                        content = Combine(
                            OneOrMore(
                                ~ignoreExpr
                                + ~Literal(opener_str)
                                + ~Literal(closer_str)
                                + CharsNotIn(ParserElement.DEFAULT_WHITE_CHARS, exact=1)
                            )
                        )
                    else:
                        content = Combine(
                            OneOrMore(
                                ~Literal(opener_str)
                                + ~Literal(closer_str)
                                + CharsNotIn(ParserElement.DEFAULT_WHITE_CHARS, exact=1)
                            )
                        )
            else:
                raise ValueError(
                    "opening and closing arguments must be strings if no content expression is given"
                )

            if ParserElement.DEFAULT_WHITE_CHARS:
                content.set_parse_action(
                    lambda t: t[0].strip(ParserElement.DEFAULT_WHITE_CHARS)
                )

        super().__init__(content, savelist=True)
        self.opener = _suppression(opener)
        self.closer = _suppression(closer)
        self.opener_raw = opener
        self.closer_raw = closer
        self.content = content
        self.ignore_expr = ignoreExpr
        self.saveAsList = True
        self.errmsg = None
        self.original_content = original_content

    def _generateDefaultName(self) -> str:
        if self.original_content is None:
            return f"nested {self.opener_raw}{self.closer_raw} expression"
        else:
            return f"nested {self.opener_raw}{self.original_content}{self.closer_raw} expression"

    def parseImpl(self, instring, loc, do_actions=True):
        loc, _ = self.opener._parse(instring, loc, do_actions=do_actions)
        stack = [[]]
        while stack:
            # 1. try ignore_expr
            if self.ignore_expr is not None:
                try:
                    loc, toks = self.ignore_expr._parse(
                        instring, loc, do_actions=do_actions
                    )
                    stack[-1].extend(toks)
                    continue
                except ParseException:
                    pass
            # 2. try opener
            try:
                loc, _ = self.opener._parse(instring, loc, do_actions=do_actions)
                stack.append([])
                continue
            except ParseException:
                pass
            # 3. try content
            try:
                next_loc, toks = self.content._parse(
                    instring, loc, do_actions=do_actions
                )
                if next_loc > loc:
                    loc = next_loc
                    stack[-1].extend(toks)
                    continue
            except ParseException:
                pass
            # 4. try closer
            try:
                loc, _ = self.closer._parse(instring, loc, do_actions=do_actions)
                top = ParseResults(stack.pop())
                if stack:
                    stack[-1].append(top)
                else:
                    return loc, ParseResults([top])
                continue
            except ParseException:
                pass

            raise ParseException(instring, loc, f"Expected {self.closer_raw!r}")


def nested_expr(
    opener: Union[str, ParserElement] = "(",
    closer: Union[str, ParserElement] = ")",
    content: typing.Optional[ParserElement] = None,
    ignore_expr: typing.Optional[ParserElement] = _NO_IGNORE_EXPR_GIVEN,
    **kwargs,
) -> ParserElement:
    """Helper method for defining nested lists enclosed in opening and
    closing delimiters (``"("`` and ``")"`` are the default).

    :param opener: str - opening character for a nested list
       (default= ``"("``); can also be a pyparsing expression

    :param closer: str - closing character for a nested list
       (default= ``")"``); can also be a pyparsing expression

    :param content: expression for items within the nested lists

    :param ignore_expr: expression for ignoring opening and closing delimiters
       (default = :class:`quoted_string`)

    Parameter ``ignoreExpr`` is retained for compatibility
    but will be removed in a future release.

    If an expression is not provided for the content argument, the
    nested expression will capture all whitespace-delimited content
    between delimiters as a list of separate values.

    Use the ``ignore_expr`` argument to define expressions that may
    contain opening or closing characters that should not be treated as
    opening or closing characters for nesting, such as quoted_string or
    a comment expression.  Specify multiple expressions using an
    :class:`Or` or :class:`MatchFirst`. The default is
    :class:`quoted_string`, but if no expressions are to be ignored, then
    pass ``None`` for this argument.

    Example:

    .. testcode::

       data_type = one_of("void int short long char float double")
       decl_data_type = Combine(data_type + Opt(Word('*')))
       ident = Word(alphas+'_', alphanums+'_')
       number = pyparsing_common.number
       arg = Group(decl_data_type + ident)
       LPAR, RPAR = map(Suppress, "()")

       code_body = nested_expr('{', '}', ignore_expr=(quoted_string | c_style_comment))

       c_function = (decl_data_type("type")
                     + ident("name")
                     + LPAR + Opt(DelimitedList(arg), [])("args") + RPAR
                     + code_body("body"))
       c_function.ignore(c_style_comment)

       source_code = '''
           int is_odd(int x) {
               return (x%2);
           }

           int dec_to_hex(char hchar) {
               if (hchar >= '0' && hchar <= '9') {
                   return (ord(hchar)-ord('0'));
               } else {
                   return (10+ord(hchar)-ord('A'));
               }
           }
       '''
       for func in c_function.search_string(source_code):
           print(f"{func.name} ({func.type}) args: {func.args}")


    prints:

    .. testoutput::

       is_odd (int) args: [['int', 'x']]
       dec_to_hex (int) args: [['char', 'hchar']]
    """
    return _NestedExpr(
        opener, closer, content=content, ignore_expr=ignore_expr, **kwargs
    )


def _makeTags(tagStr, xml, suppress_LT=Suppress("<"), suppress_GT=Suppress(">")):
    """Internal helper to construct opening and closing tag expressions,
    given a tag name"""
    if isinstance(tagStr, str_type):
        resname = tagStr
        tagStr = Keyword(tagStr, caseless=not xml)
    else:
        resname = tagStr.name

    tagAttrName = Word(alphas, alphanums + "_-:")
    if xml:
        tagAttrValue = dbl_quoted_string.copy().set_parse_action(remove_quotes)
        openTag = (
            suppress_LT
            + tagStr("tag")
            + Dict(ZeroOrMore(Group(tagAttrName + Suppress("=") + tagAttrValue)))
            + Opt("/", default=[False])("empty").set_parse_action(
                lambda s, l, t: t[0] == "/"
            )
            + suppress_GT
        )
    else:
        tagAttrValue = quoted_string.copy().set_parse_action(remove_quotes) | Word(
            printables, exclude_chars=">"
        )
        openTag = (
            suppress_LT
            + tagStr("tag")
            + Dict(
                ZeroOrMore(
                    Group(
                        tagAttrName.set_parse_action(lambda t: t[0].lower())
                        + Opt(Suppress("=") + tagAttrValue)
                    )
                )
            )
            + Opt("/", default=[False])("empty").set_parse_action(
                lambda s, l, t: t[0] == "/"
            )
            + suppress_GT
        )
    closeTag = Combine(Literal("</") + tagStr + ">", adjacent=False)

    openTag.set_name(f"<{resname}>")
    # add start<tagname> results name in parse action now that ungrouped names are not reported at two levels
    openTag.add_parse_action(
        lambda t: t.__setitem__(
            "start" + "".join(resname.replace(":", " ").title().split()), t.copy()
        )
    )
    closeTag = closeTag(
        "end" + "".join(resname.replace(":", " ").title().split())
    ).set_name(f"</{resname}>")
    openTag.tag = resname
    closeTag.tag = resname
    openTag.tag_body = SkipTo(closeTag())
    return openTag, closeTag


def make_html_tags(
    tag_str: Union[str, ParserElement],
) -> tuple[ParserElement, ParserElement]:
    """Helper to construct opening and closing tag expressions for HTML,
    given a tag name. Matches tags in either upper or lower case,
    attributes with namespaces and with quoted or unquoted values.

    Example:

    .. testcode::

       text = '<td>More info at the <a href="https://github.com/pyparsing/pyparsing/wiki">pyparsing</a> wiki page</td>'
       # make_html_tags returns pyparsing expressions for the opening and
       # closing tags as a 2-tuple
       a, a_end = make_html_tags("A")
       link_expr = a + SkipTo(a_end)("link_text") + a_end

       for link in link_expr.search_string(text):
           # attributes in the <A> tag (like "href" shown here) are
           # also accessible as named results
           print(link.link_text, '->', link.href)

    prints:

    .. testoutput::

       pyparsing -> https://github.com/pyparsing/pyparsing/wiki
    """
    return _makeTags(tag_str, False)


def make_xml_tags(
    tag_str: Union[str, ParserElement],
) -> tuple[ParserElement, ParserElement]:
    """Helper to construct opening and closing tag expressions for XML,
    given a tag name. Matches tags only in the given upper/lower case.

    Example: similar to :class:`make_html_tags`
    """
    return _makeTags(tag_str, True)


any_open_tag: ParserElement
any_close_tag: ParserElement
any_open_tag, any_close_tag = make_html_tags(
    Word(alphas, alphanums + "_:").set_name("any tag")
)

_htmlEntityMap = {k.rstrip(";"): v for k, v in html.entities.html5.items()}
_most_common_entities = "nbsp lt gt amp quot apos cent pound euro copy".replace(
    " ", "|"
)
common_html_entity = Regex(
    lambda: f"&(?P<entity>{_most_common_entities}|{make_compressed_re(_htmlEntityMap)});"
).set_name("common HTML entity")


def replace_html_entity(s, l, t):
    """Helper parser action to replace common HTML entities with their special characters"""
    return _htmlEntityMap.get(t.entity)


class OpAssoc(Enum):
    """Enumeration of operator associativity
    - used in constructing InfixNotationOperatorSpec for :class:`infix_notation`"""

    LEFT = 1
    RIGHT = 2


InfixNotationOperatorArgType = Union[
    ParserElement, str, tuple[Union[ParserElement, str], Union[ParserElement, str]]
]
InfixNotationOperatorSpec = Union[
    tuple[
        InfixNotationOperatorArgType,
        int,
        OpAssoc,
        typing.Optional[ParseAction],
    ],
    tuple[
        InfixNotationOperatorArgType,
        int,
        OpAssoc,
    ],
]


class _ParserState(Enum):
    EXPECT_OPERAND = auto()
    EXPECT_OPERATOR = auto()


class _OpType(Enum):
    PREFIX = auto()
    POSTFIX = auto()
    INFIX2 = auto()
    INFIX2_RIGHT = auto()
    TERNARY_LEFT_STAGE1 = auto()
    TERNARY_LEFT_STAGE2 = auto()
    TERNARY_RIGHT_STAGE1 = auto()
    TERNARY_RIGHT_STAGE2 = auto()
    LPAR = auto()


class _InfixNotationOperatorSpec(NamedTuple):
    op: InfixNotationOperatorArgType
    arity: int
    op_type: _OpType
    parse_action: typing.Optional[list[Callable]]


class _InfixNotation(ParseElementEnhance):
    """
    An iterative / stack-based implementation of infix_notation (using operator-precedence /
    shunting-yard style evaluation with an explicit stack).
    Prevents Python recursion limits from being exceeded on deeply nested expressions or long chains.
    """
    def __init__(
        self,
        base_expr: ParserElement,
        op_list: list[_InfixNotationOperatorSpec],
        lpar: Union[str, ParserElement] = Suppress("("),
        rpar: Union[str, ParserElement] = Suppress(")"),
    ):
        from .core import _trim_arity

        while isinstance(base_expr, _InfixNotation):
            op_list[:0] = base_expr.op_list[:]  # type: ignore[has-type]
            base_expr = base_expr.base_expr  # type: ignore[has-type]

        super().__init__(base_expr, savelist=True)
        self.base_expr = base_expr
        self.op_list = op_list
        self.lpar = Suppress(lpar) if isinstance(lpar, str) else lpar
        self.rpar = Suppress(rpar) if isinstance(rpar, str) else rpar
        self.keep_parens = not (isinstance(self.lpar, Suppress) and isinstance(self.rpar, Suppress))
        self.errmsg = None

        # Classify operators by arity and associativity
        # Precedence is defined by order in op_list (higher index in op_list = lower precedence)
        # We assign higher numeric precedence to earlier entries in op_list
        self.prefix_ops: list[_InfixNotationOperatorSpec] = []   # (expr, prec, assoc, pa_list)
        self.postfix_ops: list[_InfixNotationOperatorSpec] = []  # (expr, prec, assoc, pa_list)
        self.infix_ops = []  # type: ignore[var-annotated]

        total_ops = len(op_list)
        for idx, oper_def in enumerate(op_list):
            op_expr, arity, assoc, *pa_opt = (oper_def + (None,))[:4]
            pa = pa_opt[0] if pa_opt else None
            pa_list = (
                [_trim_arity(f) for f in pa]
                if isinstance(pa, (tuple, list))
                else ([_trim_arity(pa)] if pa is not None else [])
            )

            if not 1 <= arity <= 3:
                raise ValueError("operator must be unary (1), binary (2), or ternary (3)")

            if assoc not in (OpAssoc.LEFT, OpAssoc.RIGHT):
                raise ValueError("operator must indicate right or left associativity")

            # Precedence: top of list has highest precedence
            prec = (total_ops - idx) * 10

            if arity == 1:
                if isinstance(op_expr, str_type):
                    op_expr = Literal(op_expr)
                if assoc is OpAssoc.RIGHT:
                    self.prefix_ops.append((op_expr, prec, assoc, pa_list))
                else:
                    self.postfix_ops.append((op_expr, prec, assoc, pa_list))
            elif arity == 2:
                if op_expr is not None and isinstance(op_expr, str_type):
                    op_expr = Literal(op_expr)
                self.infix_ops.append((op_expr, prec, assoc, pa_list, 2, None))
            elif arity == 3:
                if not isinstance(op_expr, (tuple, list)) or len(op_expr) != 2:
                    raise ValueError(
                        "if numterms=3, opExpr must be a tuple or list of two expressions"
                    )
                op1, op2 = op_expr
                if isinstance(op1, str_type):
                    op1 = Literal(op1)
                if isinstance(op2, str_type):
                    op2 = Literal(op2)
                self.infix_ops.append((op1, prec, assoc, pa_list, 3, op2))

    def _generateDefaultName(self) -> str:
        return f"{self.base_expr} infix expression"

    def _run_parse_actions(self, pa_list, instring, loc, tokens):
        ret_tokens = tokens
        for fn in pa_list:
            res = fn(instring, loc, ret_tokens)
            if res is not None and res is not ret_tokens:
                if isinstance(res, (ParseResults, list, tuple)):
                    ret_tokens = ParseResults(res, aslist=True)
                else:
                    return res
        return ret_tokens

    def _apply_operator(self, op_info, operand_stack, instring):
        op_type = op_info["type"]
        pa_list = op_info.get("pa", [])
        start_loc = op_info.get("loc", 0)

        if op_type is _OpType.PREFIX:
            op_tok = op_info["op"]
            arg = operand_stack.pop()
            tokens = []
            if isinstance(op_tok, (list, ParseResults)):
                tokens.extend(op_tok)
            elif op_tok is not None:
                tokens.append(op_tok)
            tokens.append(arg)
            tokens_pr = ParseResults(tokens)
            if pa_list:
                res = self._run_parse_actions(pa_list, instring, start_loc, ParseResults([tokens_pr]))
            else:
                res = tokens_pr
            operand_stack.append(res)

        elif op_type is _OpType.POSTFIX:
            arg = operand_stack.pop()
            if isinstance(arg, ParseResults):
                res_pr = arg.copy()
            elif isinstance(arg, list):
                res_pr = ParseResults(arg)
            else:
                res_pr = ParseResults([arg])
            for op_tok in op_info["ops"]:
                if isinstance(op_tok, ParseResults):
                    res_pr += op_tok
                elif isinstance(op_tok, list):
                    res_pr.extend(op_tok)
                elif op_tok is not None:
                    res_pr.append(op_tok)
            if pa_list:
                res = self._run_parse_actions(pa_list, instring, start_loc, ParseResults([res_pr]))
            else:
                res = res_pr
            operand_stack.append(res)

        elif op_type is _OpType.INFIX2:
            ops = op_info["ops"]
            num_ops = len(ops)
            args = [operand_stack.pop() for _ in range(num_ops + 1)]
            args.reverse()
            tokens = [args[0]]
            for i in range(num_ops):
                op_tok = ops[i]
                if isinstance(op_tok, (list, ParseResults)):
                    tokens.extend(op_tok)
                elif op_tok is not None:
                    tokens.append(op_tok)
                tokens.append(args[i + 1])
            tokens_pr = ParseResults(tokens)
            if pa_list:
                res = self._run_parse_actions(pa_list, instring, start_loc, ParseResults([tokens_pr]))
            else:
                res = tokens_pr
            operand_stack.append(res)

        elif op_type is _OpType.INFIX2_RIGHT:
            op_tok = op_info["op"]
            right = operand_stack.pop()
            left = operand_stack.pop()
            tokens = [left]
            if isinstance(op_tok, (list, ParseResults)):
                tokens.extend(op_tok)
            elif op_tok is not None:
                tokens.append(op_tok)
            tokens.append(right)
            tokens_pr = ParseResults(tokens)
            if pa_list:
                res = self._run_parse_actions(pa_list, instring, start_loc, ParseResults([tokens_pr]))
            else:
                res = tokens_pr
            operand_stack.append(res)

        elif op_type is _OpType.TERNARY_LEFT_STAGE2:
            ops_list = op_info["ops"]
            num_ops = len(ops_list)
            num_operands = 2 * num_ops + 1
            args = [operand_stack.pop() for _ in range(num_operands)]
            args.reverse()
            tokens = [args[0]]
            for i in range(num_ops):
                op1_tok, op2_tok = ops_list[i]
                if isinstance(op1_tok, (list, ParseResults)):
                    tokens.extend(op1_tok)
                elif op1_tok is not None:
                    tokens.append(op1_tok)
                tokens.append(args[2 * i + 1])
                if isinstance(op2_tok, (list, ParseResults)):
                    tokens.extend(op2_tok)
                elif op2_tok is not None:
                    tokens.append(op2_tok)
                tokens.append(args[2 * i + 2])
            tokens_pr = ParseResults(tokens)
            if pa_list:
                res = self._run_parse_actions(pa_list, instring, start_loc, ParseResults([tokens_pr]))
            else:
                res = tokens_pr
            operand_stack.append(res)

        elif op_type is _OpType.TERNARY_RIGHT_STAGE2:
            op1_tok = op_info["op1"]
            op2_tok = op_info["op2"]
            arg3 = operand_stack.pop()
            arg2 = operand_stack.pop()
            arg1 = operand_stack.pop()
            tokens = [arg1]
            if isinstance(op1_tok, (list, ParseResults)):
                tokens.extend(op1_tok)
            elif op1_tok is not None:
                tokens.append(op1_tok)
            tokens.append(arg2)
            if isinstance(op2_tok, (list, ParseResults)):
                tokens.extend(op2_tok)
            elif op2_tok is not None:
                tokens.append(op2_tok)
            tokens.append(arg3)
            tokens_pr = ParseResults(tokens)
            if pa_list:
                res = self._run_parse_actions(pa_list, instring, start_loc, ParseResults([tokens_pr]))
            else:
                res = tokens_pr
            operand_stack.append(res)

        return bool(pa_list)

    def parseImpl(self, instring, loc, do_actions=True):
        operand_stack = []
        operator_stack = []
        last_pa_applied = [False]

        def reduce_operators(min_prec):
            while operator_stack:
                top = operator_stack[-1]
                if top["type"] in (_OpType.LPAR, _OpType.TERNARY_LEFT_STAGE1, _OpType.TERNARY_RIGHT_STAGE1):
                    break
                if top["prec"] > min_prec:
                    op_info = operator_stack.pop()
                    last_pa_applied[0] = self._apply_operator(op_info, operand_stack, instring)
                else:
                    break

        state = _ParserState.EXPECT_OPERAND
        paren_depth = 0

        while True:
            try:
                loc = self.preParse(instring, loc)
            except ParseException:
                pass

            if state is _ParserState.EXPECT_OPERAND:
                # 1. Try prefix operators
                matched_prefix = False
                for op_expr, prec, assoc, pa_list in self.prefix_ops:
                    try:
                        next_loc, toks = op_expr._parse(instring, loc, do_actions=do_actions)
                        op_tok = toks.as_list()[0] if len(toks) == 1 else toks.as_list()
                        operator_stack.append({
                            "type": _OpType.PREFIX,
                            "op": op_tok,
                            "prec": prec,
                            "assoc": assoc,
                            "pa": pa_list if do_actions else [],
                            "loc": loc,
                        })
                        loc = next_loc
                        matched_prefix = True
                        break
                    except ParseException:
                        pass
                if matched_prefix:
                    continue

                # 2. Try base_expr
                try:
                    next_loc, base_toks = self.base_expr._parse(instring, loc, do_actions=do_actions)
                    if not base_toks and not base_toks._tokdict:
                        loc = next_loc
                        continue
                    operand = base_toks[0] if len(base_toks) == 1 else base_toks
                    operand_stack.append(operand)
                    loc = next_loc
                    state = _ParserState.EXPECT_OPERATOR
                    continue
                except ParseException:
                    pass

                # 3. Try lpar
                try:
                    next_loc, lpar_toks = self.lpar._parse(instring, loc, do_actions=do_actions)
                    operator_stack.append({
                        "type": _OpType.LPAR,
                        "paren_toks": lpar_toks.as_list(),
                        "loc": loc,
                    })
                    paren_depth += 1
                    loc = next_loc
                    continue
                except ParseException:
                    raise ParseException(instring, loc, f"Expected {self.base_expr}")

            elif state is _ParserState.EXPECT_OPERATOR:
                # 1. Try postfix operators
                matched_postfix = False
                for op_expr, prec, assoc, pa_list in self.postfix_ops:
                    try:
                        next_loc, toks = op_expr._parse(instring, loc, do_actions=do_actions)
                        op_tok = toks
                        if (
                            operator_stack
                            and operator_stack[-1]["type"] is _OpType.POSTFIX
                            and operator_stack[-1]["prec"] == prec
                            and operator_stack[-1]["assoc"] is OpAssoc.LEFT
                        ):
                            operator_stack[-1]["ops"].append(op_tok)
                        else:
                            reduce_operators(prec)
                            operator_stack.append({
                                "type": _OpType.POSTFIX,
                                "ops": [op_tok],
                                "prec": prec,
                                "assoc": assoc,
                                "pa": pa_list if do_actions else [],
                                "loc": loc,
                            })
                        loc = next_loc
                        matched_postfix = True
                        break
                    except ParseException:
                        pass
                if matched_postfix:
                    continue

                # 2. Try rpar if inside parens
                if paren_depth > 0:
                    try:
                        next_loc, rpar_toks = self.rpar._parse(instring, loc, do_actions=do_actions)
                        reduce_operators(-1)  # reduce all operators inside this paren
                        if operator_stack and operator_stack[-1]["type"] is _OpType.LPAR:
                            lpar_info = operator_stack.pop()
                            if self.keep_parens:
                                top_val = operand_stack.pop()
                                operand_stack.append(ParseResults([*lpar_info["paren_toks"], top_val, *rpar_toks.as_list()]))
                        paren_depth -= 1
                        loc = next_loc
                        continue
                    except ParseException:
                        pass

                # 3. Try matching op2 for an open ternary operator (STAGE1)
                matched_op2 = False
                for i in range(len(operator_stack) - 1, -1, -1):
                    item = operator_stack[i]
                    if item["type"] is _OpType.LPAR:
                        break
                    if item["type"] in (_OpType.TERNARY_LEFT_STAGE1, _OpType.TERNARY_RIGHT_STAGE1):
                        try:
                            next_loc, toks = item["op2_expr"]._parse(instring, loc, do_actions=do_actions)
                            op2_tok = toks.as_list()[0] if len(toks) == 1 else toks.as_list()
                            while operator_stack and operator_stack[-1] is not item:
                                op_info = operator_stack.pop()
                                self._apply_operator(op_info, operand_stack, instring)
                            if item["type"] is _OpType.TERNARY_LEFT_STAGE1:
                                item["type"] = _OpType.TERNARY_LEFT_STAGE2
                                item["ops"][-1].append(op2_tok)
                            else:
                                item["type"] = _OpType.TERNARY_RIGHT_STAGE2
                                item["op2"] = op2_tok
                            loc = next_loc
                            matched_op2 = True
                            state = _ParserState.EXPECT_OPERAND
                            break
                        except ParseException:
                            pass
                if matched_op2:
                    continue

                def _check_operand_follows(check_loc):
                    for p_op, _, _, _ in self.prefix_ops:
                        try:
                            p_op._parse(instring, check_loc, do_actions=False)
                            return True
                        except ParseException:
                            pass
                    try:
                        self.base_expr._parse(instring, check_loc, do_actions=False)
                        return True
                    except ParseException:
                        pass
                    try:
                        self.lpar._parse(instring, check_loc, do_actions=False)
                        return True
                    except ParseException:
                        pass
                    return False

                # 4. Try infix binary and ternary operators
                matched_infix = False
                for op_expr, prec, assoc, pa_list, arity, op2_expr in self.infix_ops:
                    if arity == 2:
                        if op_expr is None:
                            if not _check_operand_follows(loc):
                                continue
                            next_loc = loc
                            op_tok = None
                        else:
                            try:
                                next_loc, toks = op_expr._parse(instring, loc, do_actions=do_actions)
                            except ParseException:
                                continue
                            if next_loc == loc:
                                if not _check_operand_follows(loc):
                                    continue
                                op_tok = (toks.as_list()[0] if len(toks) == 1 else toks.as_list()) if toks else None
                            else:
                                op_tok = toks.as_list()[0] if len(toks) == 1 else toks.as_list()

                        if assoc is OpAssoc.LEFT:
                            reduce_operators(prec)
                            if (
                                operator_stack
                                and operator_stack[-1]["type"] is _OpType.INFIX2
                                and operator_stack[-1]["prec"] == prec
                            ):
                                operator_stack[-1]["ops"].append(op_tok)
                            else:
                                operator_stack.append({
                                    "type": _OpType.INFIX2,
                                    "ops": [op_tok],
                                    "prec": prec,
                                    "assoc": assoc,
                                    "pa": pa_list if do_actions else [],
                                    "loc": loc,
                                })
                        else:
                            reduce_operators(prec)
                            operator_stack.append({
                                "type": _OpType.INFIX2_RIGHT,
                                "op": op_tok,
                                "prec": prec,
                                "assoc": assoc,
                                "pa": pa_list if do_actions else [],
                                "loc": loc,
                            })
                        loc = next_loc
                        matched_infix = True
                        state = _ParserState.EXPECT_OPERAND
                        break
                    elif arity == 3:
                        try:
                            next_loc, toks = op_expr._parse(instring, loc, do_actions=do_actions)
                            if next_loc == loc and not _check_operand_follows(loc):
                                continue
                            op_tok = toks.as_list()[0] if len(toks) == 1 else toks.as_list()
                            if assoc is OpAssoc.LEFT:
                                if (
                                    operator_stack
                                    and operator_stack[-1]["type"] is _OpType.TERNARY_LEFT_STAGE2
                                    and operator_stack[-1]["prec"] == prec
                                ):
                                    operator_stack[-1]["type"] = _OpType.TERNARY_LEFT_STAGE1
                                    operator_stack[-1]["ops"].append([op_tok])
                                else:
                                    reduce_operators(prec)
                                    operator_stack.append({
                                        "type": _OpType.TERNARY_LEFT_STAGE1,
                                        "ops": [[op_tok]],
                                        "op2_expr": op2_expr,
                                        "prec": prec,
                                        "assoc": assoc,
                                        "pa": pa_list if do_actions else [],
                                        "loc": loc,
                                    })
                            else:
                                reduce_operators(prec)
                                operator_stack.append({
                                    "type": _OpType.TERNARY_RIGHT_STAGE1,
                                    "op1": op_tok,
                                    "op2_expr": op2_expr,
                                    "prec": prec,
                                    "assoc": assoc,
                                    "pa": pa_list if do_actions else [],
                                    "loc": loc,
                                })
                            loc = next_loc
                            matched_infix = True
                            state = _ParserState.EXPECT_OPERAND
                            break
                        except ParseException:
                            pass
                if matched_infix:
                    continue

                # No more operators can be consumed at this level
                break

        # Reduce remaining operators
        reduce_operators(-1)

        if paren_depth != 0 or len(operand_stack) != 1 or operator_stack:
            raise ParseException(instring, loc, "Unbalanced parentheses or expression syntax error")

        final_result = operand_stack.pop()
        if last_pa_applied[0] and isinstance(final_result, ParseResults):
            return loc, final_result
        else:
            return loc, ParseResults([final_result])


def infix_notation(base_expr, op_list, lpar="(", rpar=")"):
    """Helper method for constructing grammars of expressions made up of
    operators working in a precedence hierarchy.  Operators may be unary
    or binary, left- or right-associative.  Parse actions can also be
    attached to operator expressions. The generated parser will also
    recognize the use of parentheses to override operator precedences
    (see example below).

    Note: if you define a deep operator list, you may see performance
    issues when using infix_notation. See
    :class:`ParserElement.enable_packrat` for a mechanism to potentially
    improve your parser performance.

    Parameters:

    :param base_expr: expression representing the most basic operand to
       be used in the expression
    :param op_list: list of tuples, one for each operator precedence level
       in the expression grammar; each tuple is of the form ``(op_expr,
       num_operands, right_left_assoc, (optional)parse_action)``, where:

       - ``op_expr`` is the pyparsing expression for the operator; may also
         be a string, which will be converted to a Literal; if ``num_operands``
         is 3, ``op_expr`` is a tuple of two expressions, for the two
         operators separating the 3 terms
       - ``num_operands`` is the number of terms for this operator (must be 1,
         2, or 3)
       - ``right_left_assoc`` is the indicator whether the operator is right
         or left associative, using the pyparsing-defined constants
         ``OpAssoc.RIGHT`` and ``OpAssoc.LEFT``.
       - ``parse_action`` is the parse action to be associated with
         expressions matching this operator expression (the parse action
         tuple member may be omitted); if the parse action is passed
         a tuple or list of functions, this is equivalent to calling
         ``set_parse_action(*fn)``
         (:class:`ParserElement.set_parse_action`)

    :param lpar: expression for matching left-parentheses; if passed as a
       str, then will be parsed as ``Suppress(lpar)``. If lpar is passed as
       an expression (such as ``Literal('(')``), then it will be kept in
       the parsed results, and grouped with them. (default= ``Suppress('(')``)
    :param rpar: expression for matching right-parentheses; if passed as a
       str, then will be parsed as ``Suppress(rpar)``. If rpar is passed as
       an expression (such as ``Literal(')')``), then it will be kept in
       the parsed results, and grouped with them. (default= ``Suppress(')')``)

    Example:

    .. testcode::

       # simple example of four-function arithmetic with ints and
       # variable names
       integer = pyparsing_common.signed_integer
       varname = pyparsing_common.identifier

       arith_expr = infix_notation(integer | varname,
           [
           ('-', 1, OpAssoc.RIGHT),
           (one_of('* /'), 2, OpAssoc.LEFT),
           (one_of('+ -'), 2, OpAssoc.LEFT),
           ])

       arith_expr.run_tests('''
           5+3*6
           (5+3)*6
           (5+x)*y
           -2--11
           ''', full_dump=False)

    prints:

    .. testoutput::
       :options: +NORMALIZE_WHITESPACE


       5+3*6
       [[5, '+', [3, '*', 6]]]

       (5+3)*6
       [[[5, '+', 3], '*', 6]]

       (5+x)*y
       [[[5, '+', 'x'], '*', 'y']]

       -2--11
       [[['-', 2], '-', ['-', 11]]]
    """
    return _InfixNotation(base_expr, op_list, lpar=lpar, rpar=rpar)


def indentedBlock(blockStatementExpr, indentStack, indent=True, backup_stacks=[]):
    """
    .. deprecated:: 3.0.0
       Use the :class:`IndentedBlock` class instead. Note that `IndentedBlock`
       has a difference method signature.

    Helper method for defining space-delimited indentation blocks,
    such as those used to define block statements in Python source code.

    :param blockStatementExpr: expression defining syntax of statement that
      is repeated within the indented block

    :param indentStack: list created by caller to manage indentation stack
      (multiple ``statementWithIndentedBlock`` expressions within a single
      grammar should share a common ``indentStack``)

    :param indent: boolean indicating whether block must be indented beyond
      the current level; set to ``False`` for block of left-most statements

    A valid block must contain at least one ``blockStatement``.

    (Note that indentedBlock uses internal parse actions which make it
    incompatible with packrat parsing.)

    Example:

    .. testcode::

       data = '''
       def A(z):
         A1
         B = 100
         G = A2
         A2
         A3
       B
       def BB(a,b,c):
         BB1
         def BBA():
           bba1
           bba2
           bba3
       C
       D
       def spam(x,y):
            def eggs(z):
                pass
       '''

       indentStack = [1]
       stmt = Forward()

       identifier = Word(alphas, alphanums)
       funcDecl = ("def" + identifier + Group("(" + Opt(delimitedList(identifier)) + ")") + ":")
       func_body = indentedBlock(stmt, indentStack)
       funcDef = Group(funcDecl + func_body)

       rvalue = Forward()
       funcCall = Group(identifier + "(" + Opt(delimitedList(rvalue)) + ")")
       rvalue << (funcCall | identifier | Word(nums))
       assignment = Group(identifier + "=" + rvalue)
       stmt << (funcDef | assignment | identifier)

       module_body = stmt[1, ...]

       parseTree = module_body.parseString(data)
       parseTree.pprint()

    prints:

    .. testoutput::

       [['def',
         'A',
         ['(', 'z', ')'],
         ':',
         [['A1'], [['B', '=', '100']], [['G', '=', 'A2']], ['A2'], ['A3']]],
        'B',
        ['def',
         'BB',
         ['(', 'a', 'b', 'c', ')'],
         ':',
         [['BB1'], [['def', 'BBA', ['(', ')'], ':', [['bba1'], ['bba2'], ['bba3']]]]]],
        'C',
        'D',
        ['def',
         'spam',
         ['(', 'x', 'y', ')'],
         ':',
         [[['def', 'eggs', ['(', 'z', ')'], ':', [['pass']]]]]]]
    """
    warnings.warn(
        f"{'indentedBlock'!r} deprecated - use {'IndentedBlock'!r}",
        PyparsingDeprecationWarning,
        stacklevel=2,
    )

    backup_stacks.append(indentStack[:])

    def reset_stack():
        indentStack[:] = backup_stacks[-1]

    def checkPeerIndent(s, l, t):
        if l >= len(s):
            return
        curCol = col(l, s)
        if curCol != indentStack[-1]:
            if curCol > indentStack[-1]:
                raise ParseException(s, l, "illegal nesting")
            raise ParseException(s, l, "not a peer entry")

    def checkSubIndent(s, l, t):
        curCol = col(l, s)
        if curCol > indentStack[-1]:
            indentStack.append(curCol)
        else:
            raise ParseException(s, l, "not a subentry")

    def checkUnindent(s, l, t):
        if l >= len(s):
            return
        curCol = col(l, s)
        if not (indentStack and curCol in indentStack):
            raise ParseException(s, l, "not an unindent")
        if curCol < indentStack[-1]:
            indentStack.pop()

    NL = OneOrMore(LineEnd().set_whitespace_chars("\t ").suppress())
    INDENT = (Empty() + Empty().set_parse_action(checkSubIndent)).set_name("INDENT")
    PEER = Empty().set_parse_action(checkPeerIndent).set_name("")
    UNDENT = Empty().set_parse_action(checkUnindent).set_name("UNINDENT")
    if indent:
        smExpr = Group(
            Opt(NL)
            + INDENT
            + OneOrMore(PEER + Group(blockStatementExpr) + Opt(NL))
            + UNDENT
        )
    else:
        smExpr = Group(
            Opt(NL)
            + OneOrMore(PEER + Group(blockStatementExpr) + Opt(NL))
            + Opt(UNDENT)
        )

    # add a parse action to remove backup_stack from list of backups
    smExpr.add_parse_action(
        lambda: backup_stacks.pop(-1) and None if backup_stacks else None
    )
    smExpr.set_fail_action(lambda a, b, c, d: reset_stack())
    blockStatementExpr.ignore(_bslash + LineEnd())
    return smExpr.set_name("indented block")


# it's easy to get these comment structures wrong - they're very common,
# so may as well make them available
c_style_comment = Regex(r"/\*(?:[^*]|\*(?!/))*\*\/").set_name("C style comment")
"Comment of the form ``/* ... */``"

html_comment = Regex(r"<!--[\s\S]*?-->").set_name("HTML comment")
"Comment of the form ``<!-- ... -->``"

rest_of_line = Regex(r".*").leave_whitespace().set_name("rest of line")
dbl_slash_comment = Regex(r"//(?:\\\n|[^\n])*").set_name("// comment")
"Comment of the form ``// ... (to end of line)``"

cpp_style_comment = Regex(
    r"(?:/\*(?:[^*]|\*(?!/))*\*\/)|(?://(?:\\\n|[^\n])*)"
).set_name("C++ style comment")
"Comment of either form :class:`c_style_comment` or :class:`dbl_slash_comment`"

java_style_comment = cpp_style_comment
"Same as :class:`cpp_style_comment`"

python_style_comment = Regex(r"#.*").set_name("Python style comment")
"Comment of the form ``# ... (to end of line)``"


# build list of built-in expressions, for future reference if a global default value
# gets updated
_builtin_exprs: list[ParserElement] = [
    v for v in vars().values() if isinstance(v, ParserElement)
]


# compatibility function, superseded by DelimitedList class
def delimited_list(
    expr: Union[str, ParserElement],
    delim: Union[str, ParserElement] = ",",
    combine: bool = False,
    min: typing.Optional[int] = None,
    max: typing.Optional[int] = None,
    *,
    allow_trailing_delim: bool = False,
) -> ParserElement:
    """
    .. deprecated:: 3.1.0
       Use the :class:`DelimitedList` class instead.
    """
    return DelimitedList(
        expr, delim, combine, min, max, allow_trailing_delim=allow_trailing_delim
    )


# Compatibility synonyms
# fmt: off
opAssoc = OpAssoc
anyOpenTag = any_open_tag
anyCloseTag = any_close_tag
commonHTMLEntity = common_html_entity
cStyleComment = c_style_comment
htmlComment = html_comment
restOfLine = rest_of_line
dblSlashComment = dbl_slash_comment
cppStyleComment = cpp_style_comment
javaStyleComment = java_style_comment
pythonStyleComment = python_style_comment
delimitedList = replaced_by_pep8("delimitedList", DelimitedList)
delimited_list = replaced_by_pep8("delimited_list", DelimitedList)
countedArray = replaced_by_pep8("countedArray", counted_array)
matchPreviousLiteral = replaced_by_pep8("matchPreviousLiteral", match_previous_literal)
matchPreviousExpr = replaced_by_pep8("matchPreviousExpr", match_previous_expr)
oneOf = replaced_by_pep8("oneOf", one_of)
dictOf = replaced_by_pep8("dictOf", dict_of)
originalTextFor = replaced_by_pep8("originalTextFor", original_text_for)
nestedExpr = replaced_by_pep8("nestedExpr", nested_expr)
makeHTMLTags = replaced_by_pep8("makeHTMLTags", make_html_tags)
makeXMLTags = replaced_by_pep8("makeXMLTags", make_xml_tags)
replaceHTMLEntity = replaced_by_pep8("replaceHTMLEntity", replace_html_entity)
infixNotation = replaced_by_pep8("infixNotation", infix_notation)
# fmt: on
