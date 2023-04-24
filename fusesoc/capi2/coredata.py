# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import copy

from fusesoc.capi2.exprs import Exprs


class CoreData:
    def __init__(self, capi_data):

        self._capi_data = capi_data or {}

        # Append all "_append" lists to the original lists. This might modify
        # _capi_data.
        self._append_lists(self._capi_data)

    def _expand_use(self, data, flags):
        if type(data) == dict:
            remove = []
            append = {}
            for k, v in data.items():
                # Only run expand() if a string contains a "?" to avoid
                # issues with strings containing for instance parentheses
                if type(v) == str and len(v) > 0 and "?" in v:
                    data[k] = Exprs(v).expand(flags)
                if type(k) == str and "?" in k:
                    expanded_k = Exprs(k).expand(flags)
                    if len(expanded_k) == 0:
                        remove.append(k)
                    elif expanded_k != k:
                        append[expanded_k] = v
                        remove.append(k)

                if type(v) == dict or type(v) == list:
                    self._expand_use(data[k], flags)

            for i in remove:
                del data[i]

            data.update(append)

        if type(data) == list:
            remove = []
            append = []
            for i in data:
                if type(i) == str and len(i) > 0 and "?" in i:
                    expanded = Exprs(i).expand(flags)
                    if i != expanded:
                        remove.append(i)
                        if len(expanded) > 0:
                            append.append(expanded)
                elif type(i) == dict or type(i) == list:
                    self._expand_use(i, flags)

            for i in remove:
                data.remove(i)

            for i in append:
                data.append(i)

    def _append_lists(self, data):
        if type(data) == list:
            for i in data:
                self._append_lists(i)

        if type(data) == dict:
            data_append = {}
            for k, v in data.items():
                if k.endswith("_append"):
                    _k = k[:-7]

                    if type(v) == list and (not _k in data or type(data[_k]) == list):
                        if _k in data:
                            # If for instance default target is included for several other
                            # targets we need to create a copy to avoid modifying the source
                            # that other targets might reference as well.
                            data[_k] = copy.deepcopy(data[_k])
                            data[_k] += v
                        else:
                            # If we have a x_append list without the corresponding x list we need
                            # to store the data temporary list since modifying the size of
                            # something during iteration will cause issues.
                            data_append[_k] = v

                self._append_lists(v)

            data.update(data_append)

    def _setup_file(self, file, fs):

        file_name = ""

        d = {
            "file_type": "",
            "copyto": "",
            "is_include_file": False,
            "include_path": "",
            "logical_name": "",
            "tags": [],
        }

        # Check if tag, file_type or logical_name are present globally in fileset
        if "tags" in fs:
            d["tags"] = fs["tags"][:]
        if "file_type" in fs:
            d["file_type"] = fs["file_type"]
        if "logical_name" in fs:
            d["logical_name"] = fs["logical_name"]

        # If we already have values for the file attributes we overwrite the defaults
        if type(file) == dict:
            for k in file.keys():
                d.update(file[k])
                file_name = k
        elif type(file) == str:
            file_name = file

        return {file_name: d}

    def _setup_fileset(self, data, flags):
        for fs in data.values():
            files = []
            for file in fs.get("files", []):
                files.append(self._setup_file(file, fs))

            if not "depend" in fs:
                fs["depend"] = []

            fs["files"] = files
            self._expand_use(fs, flags)

            # If use expansion caused any empty items we remove them
            fs["files"] = [i for i in fs["files"] if len(i) > 0]

    def _deepcopy_and_expand(self, section, flags):
        s = copy.deepcopy(self.get(section))

        self._expand_use(s, flags)

        return s

    def get(self, key, default=None):
        return self._capi_data.get(key, default)

    def get_name(self):
        return self.get("name", "")

    def get_description(self):
        return self.get("description", "")

    def get_provider(self):
        return copy.deepcopy(self.get("provider"))

    def get_filesets(self, flags):
        fs = copy.deepcopy(self.get("filesets"))

        if fs:
            self._setup_fileset(fs, flags)

        return fs or {}

    def get_generate(self, flags):
        return self._deepcopy_and_expand("generate", flags) or {}

    def get_generators(self, flags):
        return self._deepcopy_and_expand("generators", flags) or {}

    def get_scripts(self, flags):
        return self._deepcopy_and_expand("scripts", flags) or {}

    def get_targets(self, flags):
        return self._deepcopy_and_expand("targets", flags) or {}

    def get_parameters(self, flags):
        return self._deepcopy_and_expand("parameters", flags) or {}

    def get_vpi(self, flags):
        return self._deepcopy_and_expand("vpi", flags) or {}

    def get_virtual(self, flags):
        return self._deepcopy_and_expand("virtual", flags) or []
