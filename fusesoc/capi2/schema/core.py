# SPDX-License-Identifier: BSD-2-Clause
# SPDX-FileCopyrightText: FuseSoC contributors

from collections.abc import Mapping
from typing import Generic

from pydantic import Field

from .common import ExprOrStr, FrozenModel, Generator, License, Parameter, Script
from .fileset import Fileset
from .providers import Provider
from .target import GenerateInstance, Target, Vpi


class Core(FrozenModel, Generic[ExprOrStr]):
    """The top-level of the CAPI2 core schema."""

    name: str
    description: str = ""
    license: str | License | None = None
    filesets: Mapping[ExprOrStr, Fileset[ExprOrStr]] = Field(default_factory=dict)
    generate: Mapping[ExprOrStr, GenerateInstance] = Field(default_factory=dict)
    generators: Mapping[ExprOrStr, Generator] = Field(default_factory=dict)
    parameters: Mapping[ExprOrStr, Parameter[ExprOrStr]] = Field(default_factory=dict)
    provider: Provider | None = None
    scripts: Mapping[ExprOrStr, Script[ExprOrStr]] = Field(default_factory=dict)
    targets: Mapping[ExprOrStr, Target[ExprOrStr]] = Field(default_factory=dict)
    vpi: Mapping[ExprOrStr, Vpi[ExprOrStr]] = Field(default_factory=dict)
    virtual: tuple[ExprOrStr, ...] = ()
    mapping: Mapping[str, str] = Field(default_factory=dict)
