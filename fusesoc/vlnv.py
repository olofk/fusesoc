# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import copy
import re
from functools import total_ordering

_VLNV_PART_RE = re.compile(r"^[A-Za-z0-9_.-]*$")
# The dot-separated numbers a version starts with, before any pre-release
_VERSION_NUMBERS_RE = re.compile(r"\d+(?:\.\d+)*")
# The lowest version the solver gives a set of numbers, below its pre-releases
_BEFORE_PRERELEASES = ".dev0"


@total_ordering
class Vlnv:
    def __init__(self, s, default_relation=">="):
        def _is_rev(s):
            return s.startswith("r") and s[1:].isdigit()

        def _is_version(s):
            return s[0].isdigit()

        if not s:
            raise SyntaxError("Core name is empty string")

        if s.startswith("!"):
            self.conflict = True
            _s = s[1:]
        else:
            self.conflict = False
            _s = s[:]
        if not _s:
            raise SyntaxError(f"Core name is empty in '{s}'")
        if _s[0:2] in [">=", "<="]:
            self.relation = _s[0:2]
            _s = _s[2:]
        elif _s[0] in [">", "<", "~", "^"]:
            self.relation = _s[0]
            _s = _s[1:]
        elif _s[0] in ["="]:
            self.relation = "=="
            _s = _s[1:]
        else:
            self.relation = ""

        vlnv_parts = _s.split(":")

        self.revision = 0
        # legacy naming. Only name
        if len(vlnv_parts) == 1:
            self.vendor = ""
            self.library = ""
            sl = vlnv_parts[0].rsplit("-")
            if len(sl) == 1:
                # Simplest case. No '-' => Only name
                self.name = _s
                self.version = ""
            else:
                # If last part is the revision, save and pop from list
                if _is_rev(sl[-1]):
                    self.revision = int(sl.pop()[1:])

                # If last part is version, save and pop from list
                if len(sl) > 1 and _is_version(sl[-1]):
                    self.version = sl.pop()
                else:
                    self.version = ""

                self.name = "-".join(sl)

        # No version tag
        elif len(vlnv_parts) == 3:
            self.vendor = vlnv_parts[0]
            self.library = vlnv_parts[1]
            self.name = vlnv_parts[2]
            self.version = ""
        # Full vlnv
        elif len(vlnv_parts) == 4:
            self.vendor = vlnv_parts[0]
            self.library = vlnv_parts[1]
            self.name = vlnv_parts[2]
            sl = vlnv_parts[3].split("-")
            if len(sl) > 1 and _is_rev(sl[-1]):
                self.revision = int(sl.pop()[1:])
                self.version = "-".join(sl)
            else:
                self.version = vlnv_parts[3]
        else:
            raise SyntaxError(f"Illegal core name '{s}'")

        if self.version or (self.revision > 0):
            if not self.relation:
                # Version specified without relational operator
                # Assume user wants the exact version
                self.relation = "=="
            if not self.version:
                self.version = "0"
        else:
            if self.relation:
                _s = "{}: '{}' operator requires a version "
                raise SyntaxError(_s.format(s, self.relation))
            # No version specifier means any version i.e. >=0
            self.version = "0"
            self.relation = default_relation

        for field in ("vendor", "library", "name", "version"):
            value = getattr(self, field)
            if not _VLNV_PART_RE.match(value):
                raise SyntaxError(
                    "Illegal character in core name '{}': {} '{}' may only "
                    "contain alphanumerics, '.', '-', and '_'".format(s, field, value)
                )

        # Raises here, while the core is read, if a range has no numbers
        if self.relation in ("^", "~"):
            self._range_numbers()

        # Create sanitized name
        self.sanitized_name = str(self).lstrip(":").replace(":", "_")

    def __str__(self):
        revision = ""
        if self.revision > 0:
            revision = "-r" + str(self.revision)

        return "{}:{}:{}:{}{}".format(
            self.vendor, self.library, self.name, self.version, revision
        )

    __repr__ = __str__

    def __hash__(self):
        return hash(str(self))

    def depstr(self):
        if self.relation == "==":
            relation = ""
        else:
            relation = self.relation
        return relation + str(self)

    def _range_numbers(self):
        # The numbers a ^ or ~ range is computed from: those the version
        # starts with, before any pre-release
        numbers = _VERSION_NUMBERS_RE.match(self.version)
        if not numbers:
            raise SyntaxError(
                "{}: '{}' operator requires a version that starts with a "
                "number".format(self.depstr(), self.relation)
            )
        nextversion = list(map(int, numbers.group().split(".")))

        # The solver compares versions as in PEP 386. A version that is not
        # valid PEP 386 (1.0alpha1, 1.0RC1, 01.0) sorts below every valid
        # one, so as a lower bound it would let older versions into the
        # range. The version must not sort below its numbers' .dev0
        from okonomiyaki.errors import InvalidEnpkgVersion
        from okonomiyaki.versions import EnpkgVersion

        lowest = ".".join(map(str, nextversion)) + _BEFORE_PRERELEASES
        try:
            below = EnpkgVersion.from_string(
                f"{self.version}-{self.revision}"
            ) < EnpkgVersion.from_string(f"{lowest}-0")
        except InvalidEnpkgVersion:
            raise SyntaxError(
                f"{self.depstr()}: the solver cannot read version '{self.version}'"
            )
        if below:
            raise SyntaxError(
                "{}: the solver orders version '{}' below {}, so a '{}' range "
                "from it would include older versions".format(
                    self.depstr(), self.version, lowest, self.relation
                )
            )
        return nextversion

    def simpleVLNVs(self):
        if self.relation in "^~":
            # A VLNV which implies a range of versions, as in Cargo and npm
            # ^ for the same left-most non-zero number, i.e. same major
            # release from 1.0 on
            # ~ for same minor release, or same major release if the
            # version has no minor number

            # For both, we represent a >= relation on the provided
            # version...
            vlnvs = [copy.deepcopy(self)]
            vlnvs[0].relation = ">="

            # and then a second < relation on the relevant
            # field (with later fields tied low). Only the leading
            # numbers count, so ^1.0.0rc1 is <2.0.0 like ^1.0.0
            nextversion = self._range_numbers()
            if self.relation == "^":
                # The last number if they are all zero
                pos = next(
                    (i for i, n in enumerate(nextversion) if n), len(nextversion) - 1
                )
            else:
                pos = min(1, len(nextversion) - 1)
            nextversion[pos] += 1
            for i in range(pos + 1, len(nextversion)):
                nextversion[i] = 0

            vlnvs.append(copy.deepcopy(self))
            vlnvs[1].relation = "<"
            # .dev0 sorts before the next version's pre-releases (a, b, rc)
            # in the solver, so ^1.2.3 does not select 2.0.0rc1
            vlnvs[1].version = ".".join(map(str, nextversion)) + _BEFORE_PRERELEASES
            # Any revision of the next version is outside the range
            vlnvs[1].revision = 0
            return vlnvs
        else:
            # A normal VLNV, so we can return ourselves
            return [self]

    def __eq__(self, other):
        return (self.vendor, self.library, self.name, self.version) == (
            other.vendor,
            other.library,
            other.name,
            other.version,
        )

    def __lt__(self, other):
        return (self.vendor, self.library, self.name, self.version) < (
            other.vendor,
            other.library,
            other.name,
            other.version,
        )

    def vln_str(self):
        """Returns a string with <vendor>:<library>:<name>"""
        return f"{self.vendor}:{self.library}:{self.name}"


def compare_relation(vlvn_a: Vlnv, relation: str, vlvn_b: Vlnv):
    """Whether vlvn_a satisfies the relation to vlvn_b, e.g. a locked core
    against a dependency. Returns boolean."""
    from okonomiyaki.versions import EnpkgVersion

    def version_str(v):
        return f"{v.version}-{v.revision}"

    valid_version = False

    if vlvn_a.vln_str() == vlvn_b.vln_str():
        ver_a = EnpkgVersion.from_string(version_str(vlvn_a))
        ver_b = EnpkgVersion.from_string(version_str(vlvn_b))
        if relation == "==":
            valid_version = ver_a == ver_b
        elif relation == ">":
            valid_version = ver_a > ver_b
        elif relation == "<":
            valid_version = ver_a < ver_b
        elif relation == ">=":
            valid_version = ver_a >= ver_b
        elif relation == "<=":
            valid_version = ver_a <= ver_b
        elif relation in ("^", "~"):
            # The range starts at vlvn_b's version. vlvn_a must be within
            # both of its bounds, as the solver computes them.
            vlnv_range = copy.copy(vlvn_b)
            vlnv_range.relation = relation
            valid_version = all(
                compare_relation(vlvn_a, simple.relation, simple)
                for simple in vlnv_range.simpleVLNVs()
            )
    return valid_version
