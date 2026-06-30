# SPDX-License-Identifier: BSD-2-Clause
# SPDX-FileCopyrightText: FuseSoC contributors

from collections.abc import Mapping
from typing import Any, Generic

from pydantic import model_validator
from typing_extensions import TypeAliasType

from .common import ExprOrStr, FrozenModel, _merge_append_keys


class FileAttributes(FrozenModel, Generic[ExprOrStr]):
    define: Mapping[str, str | int | float | bool] | None = None
    is_include_file: bool = False
    include_path: str | None = None
    file_type: str | None = None
    logical_name: str | None = None
    tags: tuple[ExprOrStr, ...] = ()
    copyto: str | None = None


FileEntry = TypeAliasType(
    "FileEntry",
    ExprOrStr | Mapping[ExprOrStr, FileAttributes[ExprOrStr]],
    type_params=(ExprOrStr,),
)


class Fileset(FrozenModel, Generic[ExprOrStr]):
    file_type: str = ""
    logical_name: str = ""
    tags: tuple[ExprOrStr, ...] = ()
    files: tuple[FileEntry[ExprOrStr], ...] = ()
    depend: tuple[ExprOrStr, ...] = ()

    @model_validator(mode="before")
    @staticmethod
    def _merge_appends(data: Any) -> Any:
        return _merge_append_keys(data, ("files", "depend"))


def normalize_filesets(
    name, filesets: Mapping[str, Fileset[str]]
) -> Mapping[str, Fileset[str]]:
    for fs_name, fs in filesets.items():
        for file in fs.files:
            try:
                normalize_file(fs, file)
            except AssertionError:
                raise RuntimeError(f"{name} {fs_name} as a funky file: {fs}")
    return {
        fs_name: fs
        | Fileset[str](files=tuple(normalize_file(fs, file) for file in fs.files))
        for fs_name, fs in filesets.items()
    }


def normalize_file(
    fs: Fileset, file: FileEntry[str]
) -> Mapping[str, FileAttributes[str]]:
    if isinstance(file, str):
        name = file
        attrs = FileAttributes[str]()
    else:
        assert (
            len(file) == 1
        ), f"FileEntry has zero or multiple entries; there should only be one: {file}"
        [(name, attrs)] = file.items()

    return {
        name: FileAttributes[str](
            file_type=fs.file_type,
            logical_name=fs.logical_name,
            tags=fs.tags,
        )
        | attrs,
    }
