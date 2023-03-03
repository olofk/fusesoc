# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

r"""Support for parsing String expression syntax in core files

FuseSoC core files allow strings matching the following pseudo-BNF:

  exprs ::= expr
          | expr exprs

  expr ::= word
         | conditional

  word ::= [a-zA-Z0-9:<>.\[\]_-,=~/^+"]+    (one or more alphanum/special chars)

  conditional ::= condition "?" "(" exprs ")"

  condition ::= "!" word
              | word


A condition of the form "foo ? (bar)" is interpreted as 'if the "foo" flag is
set, then "bar", otherwise nothing'. Similarly, "!foo ? (bar)" is interpreted
as 'if the "foo" flag is not set then "bar", otherwise nothing'.

Expanding some exprs with a set of flags results in a space-separated string
containing each word that matched.

"""

from pyparsing import (
    Forward,
    Group,
    OneOrMore,
    Optional,
    ParseException,
    Suppress,
    Word,
    alphanums,
)


def _cond_parse_action(string, location, tokens):
    """A parse action for conditional terms"""
    # A conditional term (see _make_cond_parser) has 2 or 3 tokens, depending
    # on whether it was negated or not.
    assert len(tokens) in [2, 3]

    return (
        (True, tokens[1], tokens[2])
        if len(tokens) == 3
        else (False, tokens[0], tokens[1])
    )


_PARSER = None


def _get_parser():
    """Return a pyparsing parser for the exprs syntax

    This returns a basic "AST" that consists of a list of "exprs". Each expr is
    represented by either a string (if it's just a word) or a tuple of the form
    (negated, flag, exprs).

    Here, negated is a boolean which is true if the condition should be
    negated. flag is a word giving the flag to match for the condition. exprs
    is the AST for the list of exprs inside the parentheses.

    To avoid creating the parser repeatedly, this function is memoized.

    """
    global _PARSER
    if _PARSER is not None:
        return _PARSER

    word = Word(alphanums + '`:<>.[]_-,=~/^+"')
    exprs = Forward()

    conditional = (
        Optional("!")
        + word
        + Suppress("?")
        + Suppress("(")
        + Group(exprs)
        + Suppress(")")
    )
    exprs <<= OneOrMore(conditional ^ word)
    conditional.setParseAction(_cond_parse_action)
    _PARSER = exprs
    return _PARSER


def _simplify_ast(raw_ast):
    """Simplify an AST that comes out of the parser

    As well as replacing pyparsing's ParseResults with bare lists, this merges
    adjacent non-condition words. For example, "a b" parses to ["a", "b"]. This
    function merges that to ["a b"].

    The idea is that this will be much more efficient to match against tags for
    the vast majority of ASTs, which have many more raw words than they have
    conditions.

    A simplified AST is a list whose items are strings (representing bare
    words) or tuples of the form (negated, flag, ast), where negated is a bool,
    flag is a string and ast is another simplified ast.

    """
    children = []
    str_acc = []
    for expr in raw_ast:
        if isinstance(expr, str):
            str_acc.append(expr)
            continue

        # We have a term that isn't a string. This must be a conditional. Join
        # together any items in str_acc and add them to children then recurse
        # to simplify the conditional's sub-expression.
        if str_acc:
            children.append(" ".join(str_acc))
            str_acc = []

        negated, flag, exprs = expr
        children.append((negated, flag, _simplify_ast(exprs)))

    if str_acc:
        children.append(" ".join(str_acc))

    return children


def _parse(string):
    """Parse a string to a simplified AST.

    Raises a ValueError if the string is malformed in some way.

    """
    try:
        raw_ast = _get_parser().parseString(string, parseAll=True)
    except ParseException as err:
        raise ValueError(
            f"Invalid syntax for string: {err}. Parsed text was {string!r}."
        ) from None

    return _simplify_ast(raw_ast)


class Exprs:
    """A parsed list of exprs"""

    def __init__(self, string):
        self.ast = _parse(string)
        self.as_string = None

        # An extra optimisation for the common case where the whole ast boils
        # down to a single string with no conditions.
        if len(self.ast) == 1 and isinstance(self.ast[0], str):
            self.as_string = self.ast[0]

    @staticmethod
    def _expand(ast, flag_defs):
        """Expand ast for the given flag_defs.

        Returns a (possibly empty) list of strings

        """
        expanded = []
        for child in ast:
            if isinstance(child, str):
                expanded.append(child)
                continue

            # We have a conditional expression. Is the condition true? If not,
            # skip it.
            negated, flag, exprs = child
            if (flag in flag_defs) == negated:
                # The condition was false
                continue

            # The condition was true
            expanded += Exprs._expand(exprs, flag_defs)
        return expanded

    @staticmethod
    def _flags_to_flag_defs(flags):
        """Convert a flags dictionary to the set of flags that are defined"""
        ret = []
        for k, v in flags.items():
            if v is True:
                ret.append(k)
            elif v not in [False, None]:
                ret.append(k + "_" + v)
        return set(ret)

    def expand(self, flags):
        """Expand the parsed string in the presence of the given flags"""
        if self.as_string is not None:
            return self.as_string

        flag_defs = Exprs._flags_to_flag_defs(flags)
        return " ".join(Exprs._expand(self.ast, flag_defs))
