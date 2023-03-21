# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

# FIXME: Read schema from file or internet instead
from fusesoc.capi2.json_schema import capi2_schema
from fusesoc.parser.coreparser import CoreParser


class Core2Parser(CoreParser):
    def __init__(self, resolve_env_vars=False, allow_additional_properties=False):
        self.capi_version = 2
        self.preamble = "CAPI=2:"
        self.schema = capi2_schema

        CoreParser.__init__(
            self,
            self.preamble,
            self.schema,
            self.capi_version,
            resolve_env_vars,
            allow_additional_properties,
        )
