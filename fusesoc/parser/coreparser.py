# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import fastjsonschema
import yaml

from fusesoc import utils


class CoreParser:
    def __init__(
        self,
        preamble,
        schema,
        version,
        resolve_env_vars=False,
        allow_additional_properties=False,
    ):
        self._preamble = preamble
        self._schema = schema
        self._version = version
        self._resolve_env_vars = resolve_env_vars
        self._allow_additional_properties = allow_additional_properties

        self._schema_data = utils.yaml_read(schema)

        if allow_additional_properties:
            self._set_additional_properties(self._schema_data, True)

        try:
            self._validate = fastjsonschema.compile(self._schema_data)
        except fastjsonschema.JsonSchemaDefinitionException as e:
            raise SyntaxError(f"\nError parsing JSON Schema: {e}")

    def _set_additional_properties(self, schema, val):
        if type(schema) == list:
            for i in schema:
                self._set_additional_properties(i, val)

        if type(schema) == dict:
            for k, v in schema.items():
                if k == "additionalProperties" and type(v) == bool:
                    schema[k] = val

                if type(v) == dict or type(v) == list:
                    self._set_additional_properties(v, val)

    def read(self, core_file, validate_core=True):
        capi_data = utils.yaml_fread(core_file, self._resolve_env_vars, True)

        if validate_core:
            self.validate(capi_data)

        return capi_data

    def write(self, core_file, capi_data, validate_core=True):
        if validate_core:
            self.validate(capi_data)

        utils.yaml_fwrite(core_file, capi_data, self._preamble)

    def validate(self, capi_data):
        try:
            self._validate(capi_data)
        except fastjsonschema.JsonSchemaException as e:
            raise SyntaxError(f"\nError validating {e}")

    def get_version(self):
        return self._version

    def get_preamble(self):
        return self._preamble

    def get_schema(self):
        return self._schema

    def get_allow_additional_properties(self):
        return self._allow_additional_properties
