# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import pytest

from fusesoc.capi2.exprs import Exprs


def check_parses_to(string, ast):
    assert Exprs(string).ast == ast


def check_parse_error(string):
    with pytest.raises(ValueError) as err:
        Exprs(string)
    assert "Invalid syntax for string:" in str(err.value)


def test_exprs():
    check_parses_to("a", ["a"])
    check_parses_to("a b", ["a b"])
    check_parses_to("a+b", ["a+b"])
    check_parses_to("a ? (b)", [(False, "a", ["b"])])
    check_parses_to("a ? (b c)", [(False, "a", ["b c"])])
    check_parses_to("a ? (b ? (c))", [(False, "a", [(False, "b", ["c"])])])
    check_parses_to("!a ? (b)", [(True, "a", ["b"])])
    check_parses_to("a b ? (c)", ["a", (False, "b", ["c"])])
    check_parses_to('a"b"', ['a"b"'])

    check_parse_error("!a")
    check_parse_error("a ? b")
    check_parse_error("a !b")


def check_expand(string, flags, expansion):
    assert Exprs(string).expand(flags) == expansion


def test_expand():
    check_expand("a", {}, "a")
    check_expand("a ? (b)", {}, "")
    check_expand("!a ? (b)", {}, "b")

    check_expand("a ? (b)", {"a": True}, "b")
    check_expand("!a ? (b)", {"a": True}, "")

    check_expand("a ? (b)", {"a": False}, "")
    check_expand("!a ? (b)", {"a": False}, "b")

    check_expand("mode_foo ? (a)", {"mode": "foo"}, "a")
    check_expand("mode_foo ? (a)", {"mode": "bar"}, "")
    check_expand("!mode_foo ? (a)", {"mode": "foo"}, "")
    check_expand("!mode_foo ? (a)", {"mode": "bar"}, "a")
