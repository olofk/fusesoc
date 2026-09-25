# SPDX-License-Identifier: BSD-2-Clause
# SPDX-FileCopyrightText: FuseSoC contributors

import logging
from collections.abc import Mapping
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, model_validator
from typing_extensions import Self

from ..exprs import Expr

logger = logging.getLogger(__name__)


class FrozenModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="allow",
    )

    def __or__(self, other: Self) -> Self:
        """This allows easy editing of FrozenModels.

        Instead of having to construct a FrozenModel by specifying
        the value for each field in a constructor. One can just 'or' it
        with just the fields they would like updating.
        `|=` can also be used without modifying the original object.

        Example::
          new = old | Frozen(new_field=42)
        """
        return self.model_copy(
            update={name: getattr(other, name) for name in other.model_fields_set}
        )


ExprOrStr = TypeVar("ExprOrStr", str, Expr)


def _merge_append_keys(
    data: Any, keys: tuple[str, ...], info: ValidationInfo | None = None
) -> Any:
    """Merge `<key>_append` lists into `<key>` lists at parse time.

    Items already present in the base list (or repeated within the
    `<key>_append` list itself) are dropped with a warning, so a fileset
    or file pulled in twice through target inheritance is only emitted
    once (see #767)."""
    if not isinstance(data, dict):
        return data
    core_file = (info.context or {}).get("core_file") if info else None
    for key in keys:
        ak = f"{key}_append"
        if ak in data:
            base = list(data.get(key, []))
            for item in data.pop(ak):
                if item in base:
                    source = f" in {core_file}" if core_file else ""
                    logger.warning(
                        f"Dropping duplicate entry '{item}' from '{ak}'{source}"
                    )
                else:
                    base.append(item)
            data[key] = base
    return data


class License(FrozenModel):
    name: str
    text: str


class Generator(FrozenModel):
    """Definition of a generator that other cores can invoke."""

    command: str
    interpreter: str | None = None
    cache_type: Literal["none", "input", "generator"] | None = None
    file_input_parameters: str | None = None
    description: str | None = None
    usage: str | None = None


class Parameter(FrozenModel, Generic[ExprOrStr]):
    datatype: Literal["bool", "file", "int", "real", "str"]
    paramtype: ExprOrStr
    default: bool | str | int | float | None = None
    description: str | None = None
    scope: str | None = None  # backwards-compat, unused


class Script(FrozenModel, Generic[ExprOrStr]):
    env: Mapping[str, str] = Field(default_factory=dict)
    cmd: tuple[ExprOrStr, ...] = ()
    filesets: tuple[ExprOrStr, ...] = ()

    @model_validator(mode="before")
    @staticmethod
    def _merge_appends(data: Any, info: ValidationInfo) -> Any:
        return _merge_append_keys(data, ("cmd", "filesets"), info)
