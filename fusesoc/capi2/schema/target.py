# SPDX-License-Identifier: BSD-2-Clause
# SPDX-FileCopyrightText: FuseSoC contributors

from collections.abc import Mapping
from typing import Any, Generic, Literal

from pydantic import Field, JsonValue, model_validator

from ..flags import Flags
from .common import ExprOrStr, FrozenModel, _merge_append_keys


class GenerateInstance(FrozenModel):
    """An instance of a generator invoked by a target."""

    generator: str
    parameters: Mapping[str, JsonValue] = Field(default_factory=dict)
    position: Literal["first", "prepend", "append", "last"] | None = None


class Hooks(FrozenModel, Generic[ExprOrStr]):
    pre_build: tuple[ExprOrStr, ...] = ()
    post_build: tuple[ExprOrStr, ...] = ()
    pre_run: tuple[ExprOrStr, ...] = ()
    post_run: tuple[ExprOrStr, ...] = ()

    @model_validator(mode="before")
    @staticmethod
    def _merge_appends(data: Any) -> Any:
        return _merge_append_keys(
            data, ("pre_build", "post_build", "pre_run", "post_run")
        )


class Vpi(FrozenModel, Generic[ExprOrStr]):
    filesets: tuple[ExprOrStr, ...] = ()
    libs: tuple[ExprOrStr, ...] = ()

    @model_validator(mode="before")
    @staticmethod
    def _merge_appends(data: Any) -> Any:
        return _merge_append_keys(data, ("filesets", "libs"))


class Target(FrozenModel, Generic[ExprOrStr]):
    default_tool: str | None = None
    description: str = ""
    flow: str | None = None
    flow_options: Mapping[str, JsonValue] = Field(default_factory=dict)
    tools: Mapping[ExprOrStr, Mapping[str, JsonValue]] = Field(default_factory=dict)
    flags: Flags = Field(default_factory=dict)
    hooks: Hooks[ExprOrStr] = Field(default_factory=Hooks)
    toplevel: tuple[ExprOrStr, ...] = ()
    filesets: tuple[ExprOrStr, ...] = ()
    filters: tuple[ExprOrStr, ...] = ()
    parameters: tuple[ExprOrStr, ...] = ()
    vpi: tuple[ExprOrStr, ...] = ()
    generate: tuple[ExprOrStr | Mapping[str, JsonValue], ...] = ()

    @model_validator(mode="before")
    @staticmethod
    def _normalize(data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = _merge_append_keys(
            data, ("filesets", "filters", "parameters", "vpi", "generate")
        )
        if "toplevel" in data and isinstance(data["toplevel"], str):
            data = {**data, "toplevel": (data["toplevel"],)}
        return data
