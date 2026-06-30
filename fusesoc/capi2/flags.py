# SPDX-License-Identifier: BSD-2-Clause
# SPDX-FileCopyrightText: FuseSoC contributors

from typing import Mapping

from pydantic import validate_call

FlagValue = bool | str | int | None
Flags = Mapping[str, FlagValue]
FlagDefs = frozenset[str]


@validate_call
def into_flag_defs(flags: Flags) -> FlagDefs:
    ret = []
    for k, v in flags.items():
        if v is True:
            ret.append(k)
        elif isinstance(v, (str, int)):
            ret.append(k + "_" + str(v))
    return frozenset(ret)


def get_target_name(flags: Flags) -> str:
    if flags.get("is_toplevel") and (target := flags.get("target")):
        assert isinstance(target, str), "Target must be a string."
        return target
    else:
        return "default"
