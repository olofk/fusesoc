# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import pytest

from fusesoc.vlnv import Vlnv, compare_relation


def vlnv_tuple(vlnv):
    return (vlnv.vendor, vlnv.library, vlnv.name, vlnv.version, vlnv.revision)


# VLNV tests without revision
def test_full_vlnv():
    assert vlnv_tuple(Vlnv("librecores.org:peripherals:uart16550:1.5")) == (
        "librecores.org",
        "peripherals",
        "uart16550",
        "1.5",
        0,
    )


def test_full_vlnv_no_version():
    assert vlnv_tuple(Vlnv("librecores.org:peripherals:uart16550")) == (
        "librecores.org",
        "peripherals",
        "uart16550",
        "0",
        0,
    )


def test_name_only_vlnv():
    assert vlnv_tuple(Vlnv("::uart16550")) == ("", "", "uart16550", "0", 0)
    assert vlnv_tuple(Vlnv("::uart16550:")) == ("", "", "uart16550", "0", 0)


def test_name_version_vlnv():
    assert vlnv_tuple(Vlnv("::uart16550:1.5")) == ("", "", "uart16550", "1.5", 0)


# VLNV tests with revision
def test_full_vlnv_revision():
    assert vlnv_tuple(Vlnv("librecores.org:peripherals:uart16550:1.5-r5")) == (
        "librecores.org",
        "peripherals",
        "uart16550",
        "1.5",
        5,
    )


def test_name_only_vlnv_revision():
    assert vlnv_tuple(Vlnv("::uart16550")) == ("", "", "uart16550", "0", 0)
    assert vlnv_tuple(Vlnv("::uart16550:")) == ("", "", "uart16550", "0", 0)


# Tests for legacy naming scheme
def test_name_version_legacy():
    assert vlnv_tuple(Vlnv("uart16550-1.5")) == ("", "", "uart16550", "1.5", 0)


def test_name_with_dash_version_legacy():
    assert vlnv_tuple(Vlnv("wb-axi-1.5")) == ("", "", "wb-axi", "1.5", 0)


def test_name_only_legacy():
    assert vlnv_tuple(Vlnv("uart16550")) == ("", "", "uart16550", "0", 0)


def test_name_with_dash_only_legacy():
    assert vlnv_tuple(Vlnv("wb-axi")) == ("", "", "wb-axi", "0", 0)


def test_name_version_revision_legacy():
    assert vlnv_tuple(Vlnv("uart16550-1.5-r2")) == ("", "", "uart16550", "1.5", 2)


def test_name_revision_legacy():
    assert vlnv_tuple(Vlnv("uart16550-r2")) == ("", "", "uart16550", "0", 2)


# Reject names containing characters that downstream parsers cannot handle.
# Regression tests for https://github.com/olofk/fusesoc/issues/749
@pytest.mark.parametrize(
    "bad_name",
    [
        "a/b",
        "::a/b",
        "vend/or:lib:name",
        "::a b:0",
        "::na\tme",
        "foo*:lib:name:0",
    ],
)
def test_vlnv_rejects_illegal_chars(bad_name):
    with pytest.raises(SyntaxError, match="Illegal character"):
        Vlnv(bad_name)


@pytest.mark.parametrize(
    "dependency, lower, upper",
    [
        ("^::x:1.2.3", "::x:1.2.3", "::x:2.0.0"),
        # Before 1.0, ^ keeps the left-most non-zero number
        ("^::x:0.2.3", "::x:0.2.3", "::x:0.3.0"),
        ("^::x:0.0.3", "::x:0.0.3", "::x:0.0.4"),
        ("^::x:0.0", "::x:0.0", "::x:0.1"),
        ("^::x:0", "::x:0", "::x:1"),
        ("~::x:1.2.3", "::x:1.2.3", "::x:1.3.0"),
        ("~::x:1.2", "::x:1.2", "::x:1.3"),
        # With no minor number, ~ allows minor updates
        ("~::x:1", "::x:1", "::x:2"),
        # The upper bound has no revision: 2.0.0-r0 is outside the range too
        ("^::x:1.2.3-r1", "::x:1.2.3-r1", "::x:2.0.0"),
        ("~::x:1.2.3-r2", "::x:1.2.3-r2", "::x:1.3.0"),
    ],
)
def test_vlnv_range(dependency, lower, upper):
    low, high = Vlnv(dependency).simpleVLNVs()
    assert (low.relation, str(low)) == (">=", lower)
    assert (high.relation, str(high)) == ("<", upper)


def test_vlnv_rejects_bare_conflict():
    with pytest.raises(SyntaxError, match="Core name is empty"):
        Vlnv("!")


@pytest.mark.parametrize(
    "dependency, relation, version",
    [
        ("!::x", ">=", "0"),
        ("!x", ">=", "0"),
        ("!::x:1.2", "==", "1.2"),
        ("!=::x:1.2", "==", "1.2"),
        ("!>=::x:1.2", ">=", "1.2"),
        ("!~::x:1.2", "~", "1.2"),
    ],
)
def test_vlnv_conflict(dependency, relation, version):
    vlnv = Vlnv(dependency)
    assert vlnv.conflict
    assert (vlnv.relation, vlnv.vln_str(), vlnv.version) == (relation, "::x", version)


def test_vlvn_compare_relation():
    version_1_3 = Vlnv(":peripherals:uart16550:1.3.1")
    version_1_4 = Vlnv(":peripherals:uart16550:1.4.2")
    version_1_5 = Vlnv(":peripherals:uart16550:1.5.1")
    version_2_0 = Vlnv(":peripherals:uart16550:2.0.1")

    assert compare_relation(version_1_4, "==", version_1_4)
    assert not compare_relation(
        version_1_4, "==", Vlnv("other:peripherals:uart16550:1.4.2")
    )
    assert not compare_relation(version_1_4, "==", Vlnv(":other:uart16550:1.4.2"))
    assert not compare_relation(version_1_4, "==", Vlnv(":peripherals:other:1.4.2"))
    assert not compare_relation(version_1_4, "==", version_1_3)
    assert not compare_relation(version_1_4, "==", version_1_5)
    assert not compare_relation(version_1_4, "==", version_2_0)

    assert compare_relation(version_1_4, ">", version_1_3)
    assert not compare_relation(version_1_4, ">", version_1_4)
    assert not compare_relation(version_1_4, ">", version_1_5)
    assert not compare_relation(version_1_4, ">", version_2_0)

    assert compare_relation(version_1_4, ">=", version_1_3)
    assert compare_relation(version_1_4, ">=", version_1_4)
    assert not compare_relation(version_1_4, ">=", version_1_5)
    assert not compare_relation(version_1_4, ">=", version_2_0)

    assert not compare_relation(version_1_4, "<", version_1_3)
    assert not compare_relation(version_1_4, "<", version_1_4)
    assert compare_relation(version_1_4, "<", version_1_5)
    assert compare_relation(version_1_4, "<", version_2_0)

    assert not compare_relation(version_1_4, "<=", version_1_3)
    assert compare_relation(version_1_4, "<=", version_1_4)
    assert compare_relation(version_1_4, "<=", version_1_5)
    assert compare_relation(version_1_4, "<=", version_2_0)

    # A range starts at the second VLNV's version, like the other relations
    assert not compare_relation(version_1_3, "^", version_1_4)
    assert compare_relation(version_1_4, "^", version_1_4)
    assert compare_relation(version_1_5, "^", version_1_4)
    assert not compare_relation(version_2_0, "^", version_1_4)

    assert not compare_relation(version_1_3, "~", version_1_4)
    assert compare_relation(version_1_4, "~", version_1_4)
    assert compare_relation(Vlnv(":peripherals:uart16550:1.4.9"), "~", version_1_4)
    assert not compare_relation(version_1_5, "~", version_1_4)
    assert not compare_relation(version_2_0, "~", version_1_4)
