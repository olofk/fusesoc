# SPDX-License-Identifier: BSD-2-Clause
# SPDX-FileCopyrightText: FuseSoC contributors

from dataclasses import dataclass, field
from typing import Any

from fusesoc.capi2.schema.core import Core
from fusesoc.capi2.schema.fileset import normalize_filesets

from .exprs import Expr
from .flags import FlagDefs


def evaluate_exprs(data: Any, defs: FlagDefs) -> Any:
    """Pure, non-mutating use-flag expansion."""
    match data:
        case dict():
            result: dict[Any, Any] = {}
            for k, v in data.items():
                if isinstance(v, Expr):
                    new_v: Any = v.expand(defs)
                elif isinstance(v, (dict, list, tuple)):
                    new_v = evaluate_exprs(v, defs)
                else:
                    new_v = v

                if isinstance(k, Expr):
                    new_k = k.expand(defs)
                    if not new_k:
                        continue
                else:
                    new_k = k

                result[new_k] = new_v
            return result

        case list() | tuple():
            out: list[Any] = []
            for item in data:
                if isinstance(item, Expr):
                    expanded = item.expand(defs)
                    if expanded:
                        out.append(expanded)
                elif isinstance(item, (dict, list, tuple)):
                    expanded_item = evaluate_exprs(item, defs)
                    # If expression evaluation results in an empty container,
                    # ignore the container.
                    if expanded_item:
                        out.append(expanded_item)
                else:
                    out.append(item)
            return tuple(out) if isinstance(data, tuple) else out

        case _:
            return data


def expand_exprs(core: Core[Expr], flag_defs: FlagDefs) -> "Core[str]":
    dumped = core.model_dump(mode="python", exclude_unset=True, by_alias=True)
    expanded = evaluate_exprs(dumped, flag_defs)

    expanded_core = Core[str].model_validate(expanded)

    return expanded_core | Core[str](
        name=expanded_core.name,
        filesets=normalize_filesets(expanded_core.name, expanded_core.filesets),
    )


@dataclass
class CoreHandle:
    _raw: Core[Expr]
    _cache: dict[FlagDefs, Core[str]] = field(init=False, default_factory=dict)

    @classmethod
    def from_dict(cls, capi_dict: dict) -> "CoreHandle":
        return cls(Core[Expr].model_validate(capi_dict))

    def get(self, flag_defs: FlagDefs) -> Core[str]:
        if core := self._cache.get(flag_defs):
            return core

        core = expand_exprs(self._raw, flag_defs)
        self._cache[flag_defs] = core
        return core
