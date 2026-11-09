# SPDX-License-Identifier: BSD-2-Clause
# SPDX-FileCopyrightText: FuseSoC contributors

from typing import Annotated, Literal, Union

from pydantic import Field

from .common import FrozenModel

SHA256_PATTERN = "^[0-9a-fA-F]{64}$"


class GithubProvider(FrozenModel):
    name: Literal["github"]
    user: str
    repo: str
    version: str
    patches: tuple[str, ...] = ()
    cachable: bool | None = None


class LocalProvider(FrozenModel):
    name: Literal["local"]
    patches: tuple[str, ...] = ()
    cachable: bool | None = None


class GitProvider(FrozenModel):
    name: Literal["git"]
    repo: str
    version: str | None = None
    patches: tuple[str, ...] = ()
    cachable: bool | None = None


class OpencoresProvider(FrozenModel):
    name: Literal["opencores"]
    repo_name: str
    repo_root: str
    revision: str
    patches: tuple[str, ...] = ()
    cachable: bool | None = None


class SvnProvider(FrozenModel):
    name: Literal["svn"]
    url: str
    revision: str | None = None
    ignore_externals: bool | None = None
    patches: tuple[str, ...] = ()
    cachable: bool | None = None


class UrlProvider(FrozenModel):
    name: Literal["url"]
    url: str
    user_agent: str | None = Field(default=None, alias="user-agent")
    verify_cert: str | None = None
    filetype: str
    # The download's hash, checked before it is unpacked.
    sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    patches: tuple[str, ...] = ()
    cachable: bool | None = None


Provider = Annotated[
    Union[
        GithubProvider,
        LocalProvider,
        GitProvider,
        OpencoresProvider,
        SvnProvider,
        UrlProvider,
    ],
    Field(discriminator="name"),
]
