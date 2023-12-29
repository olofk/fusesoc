import yaml
from typing import List, Dict, Optional, Literal, Union
from pydantic import BaseModel, Field


class BaseProvider(BaseModel):
    name: str
    patches: Optional[List[str]]=Field(default=[], description='''
        List of patches to apply automatically.''',
    )
    cachable: Optional[bool]=Field(default=True, description='''
        Is the provider cacheable.''',
    )


class ProviderGithub(BaseProvider):
    class Config:
        extra = 'forbid'

    name: Literal['github']
    user: str
    repo: str
    version: str


class ProviderLocal(BaseProvider):
    class Config:
        extra = 'forbid'

    name: Literal['local']


class ProviderGit(BaseProvider):
    class Config:
        extra = 'forbid'

    name: Literal['git']
    repo: str
    version: Optional[str]=Field(default=None)


class ProviderOpencores(BaseProvider):
    class Config:
        extra = 'forbid'

    name: Literal['opencores']
    repo_name: str
    repo_root: str
    revision: str


class ProviderUserAgent(BaseProvider):
    class Config:
        extra = 'forbid'

    name: Literal['url']
    url: str
    user_agent: Optional[str]=Field(default=None, alias='user-agent')
    verify_cert: Optional[bool]=Field(default=True, description='''
        Optionally skip Certificate verification.''',
    )
    filetype: str


Provider = Optional[Union[
    ProviderGithub,
    ProviderLocal,
    ProviderGit,
    ProviderOpencores,
    ProviderUserAgent,
]]


class Files(BaseModel):
    class Config:
        extra = 'allow'

    is_include_file: Optional[bool]=Field(default=None, description='''
        Treats file as an include file when true''',
    )
    include_path: Optional[str]=Field(default=None, description='''
        Explicitly set an include directory, relative to core root, instead of
        the directory containing the file.''',
    )
    file_type: Optional[str] = Field(default=None, description='''
        File type. Overrides the file_type set on the containing fileset''',
    )
    logical_name: Optional[str] = Field(default=None, description='''
        Logical name, i.e. library for VHDL/SystemVerilog. Overrides the
        logical_name set on the containing fileset''',
    )
    tags: Optional[List[str]] = Field(default=None, description='''
        Tags, special file-specific hints for the backends. Appends the tags
        set on the containing fileset''',
    )
    copyto: Optional[str] = Field(default=None, description='''
        Copy the source file to this path in the work directory.''',
    )


class Fileset(BaseModel):
    class Config:
        extra = 'forbid'

    file_type: Optional[str]=Field(default=None, description='''
        Default file_type for files in fileset''',
    )
    logical_name: Optional[str]=Field(default=None, description='''
        Default logical_name (i.e. library) for files in fileset''',
    )
    tags: Optional[List[str]]=Field(default=None, description='''
        Default tags for files in fileset''',
    )
    files: Optional[List[Union[str, Dict[str, Files]]]]=Field(None, description='''
        Files in fileset''',
    )


class CAPI2(BaseModel):
    CAPI2: Literal[None]=Field(alias='CAPI=2')
    name: str=Field(description='VLNV identifier for core')
    description: Optional[str] = Field(description='Short description of core')
    provider: Optional[Provider] = Field(default=None, discriminator='name', description='''
        Provider of core''',
    )
    filesets: Dict[str, Fileset]=Field(description='''
        A fileset represents a group of files with a common purpose.

        Each file in the fileset is required to have a file type and is allowed
        to have a logical_name which can be set for the whole fileset or
        individually for each file. A fileset can also have dependencies on
        other cores, specified in the depend section.''',
    )
