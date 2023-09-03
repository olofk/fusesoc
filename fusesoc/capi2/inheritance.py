# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import copy
import re

from fusesoc import utils


class Inheritance:
    MERGE_OPERATOR = "<<__FUSESOC_MERGE_OVERLOAD__<<"

    def yaml_merge_2_fusesoc_merge(capi):
        """
        Replace YAML merge key operator (<<) with FuseSoC merge operator
        """
        yaml_merge_pattern = (
            r"((?:\n|{|\{\s*(?:[^{}]*\{[^{}]*\})*[^{}]*\},)\s*)<<(?=\s*:)"
        )
        while re.search(yaml_merge_pattern, capi):
            capi = re.sub(yaml_merge_pattern, r"\1" + Inheritance.MERGE_OPERATOR, capi)
        return capi

    def elaborate_inheritance(capi):
        if not isinstance(capi, dict):
            return capi

        for key, value in capi.items():
            if isinstance(value, dict):
                capi[key] = Inheritance.elaborate_inheritance(copy.deepcopy(value))

        parent = capi.pop(Inheritance.MERGE_OPERATOR, {})
        if isinstance(parent, dict):
            capi = utils.merge_dict(parent, capi, concat_list_appends_only=True)
        else:
            raise SyntaxError("Invalid use of inheritance operator")

        return capi
