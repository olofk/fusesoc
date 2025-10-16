#!/usr/bin/env python
# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import datetime
import hashlib
import json
import os

import nanoid


class Spdxgen:
    no_assertion_id = "https://FuseSoC/license/noAssertion"

    def _generate_preamble(self, ci_id, now):
        ei_id = "https://FuseSoC/externalid/" + nanoid.generate()
        doc_id = "https://FuseSoC/document/" + nanoid.generate()
        bom_id = "https://FuseSoC/document/" + nanoid.generate()

        preamble = [
            # Creation info and children
            {
                # The id of the creating agent (this program) is
                # hardcoded.  Should probably be a generated hash.
                "type": "CreationInfo",
                "created": now,
                "createdBy": "https://FuseSoC/program/3mLEPOMKT/Q3QmuONJ+QuQ",
                "spdx:Core/specVersion": "3.0.1",
                "@id": ci_id,
            },
            {
                # The id of the external identifier for the creating
                # agent is random for each run.  This makes no
                # particular sense.
                "spdxId": "https://FuseSoC/program/3mLEPOMKT/Q3QmuONJ+QuQ",
                "type": "SoftwareAgent",
                "creationInfo": ci_id,
                "externalIdentifier": ei_id,
                "spdx:Core/name": "FuseSoC",
            },
            {
                "type": "ExternalIdentifier",
                "externalIdentifierType": "other",
                "spdx:Core/identifier": "https://github.com/olofk/fusesoc/",
                "@id": ei_id,
            },
            # "NoAssertion" license to reference anywhere one is needed.
            {
                "spdxId": self.no_assertion_id,
                "type": "simplelicensing_LicenseExpression",
                "creationInfo": ci_id,
                "spdx:SimpleLicensing/licenseExpression": "No assertion",
            },
            # Document and sbom
            {
                "spdxId": doc_id,
                "type": "SpdxDocument",
                "creationInfo": ci_id,
                "profileConformance": ["core", "lite"],
                "rootElement": bom_id,
            },
            {
                "spdxId": bom_id,
                "type": "software_Sbom",
                "creationInfo": ci_id,
                "rootElement": "",  # Filled in later
                "element": [],  # Filled in later
                "software_sbomType": "source",
            },
        ]
        return preamble, preamble[-1]

    def _generate_package(self, work_root, ci_id, vlnv, license_expr, flist):
        [vln, version] = vlnv.rsplit(":", 1)
        [vendor, library, name] = vln.split(":")

        concl_license_id = "https://FuseSoC/license/" + nanoid.generate()
        concl_license_rel_id = "https://FuseSoC/relationship/" + nanoid.generate()
        decl_license_rel_id = "https://FuseSoC/relationship/" + nanoid.generate()
        purl = f"pkg:fusesoc/{vendor}/{library}/{name}@{version}"
        pkg_id = "https://FuseSoC/package/" + vlnv
        pkg = [
            {
                "spdxId": pkg_id,
                "type": "software_Package",
                "creationInfo": ci_id,
                "spdx:Core/name": vln,
                "software_packageUrl": purl,
                "spdx:Software/packageVersion": version,
            },
            # Declared license, hardcoded NoAssertion
            {
                "spdxId": decl_license_rel_id,
                "type": "Relationship",
                "creationInfo": ci_id,
                "from": pkg_id,
                "relationshipType": "hasDeclaredLicense",
                "to": self.no_assertion_id,
            },
            # Concluded license, from core file
            {
                "spdxId": concl_license_id,
                "type": "simplelicensing_LicenseExpression",
                "creationInfo": ci_id,
                "spdx:SimpleLicensing/licenseExpression": license_expr,
            },
            {
                "spdxId": concl_license_rel_id,
                "type": "Relationship",
                "creationInfo": ci_id,
                "from": pkg_id,
                "relationshipType": "hasConcludedLicense",
                "to": concl_license_id,
            },
            {
                "spdxId": "relationShip:" + vlnv + ":files",
                "type": "Relationship",
                "creationInfo": ci_id,
                "from": pkg_id,
                "relationshipType": "contains",
                "to": [],
            },
        ]
        file_rel = pkg[-1]
        for fname in flist:
            file_id = "https://FuseSoC/file/" + nanoid.generate()
            hash_id = "https://FuseSoC/hash/" + nanoid.generate()
            with open(os.path.join(work_root, fname), "rb", buffering=0) as f:
                hash_val = hashlib.file_digest(f, "sha256").hexdigest()
            pkg += [
                {
                    "spdxId": file_id,
                    "type": "software_File",
                    "creationInfo": ci_id,
                    "spdx:Core/name": fname,
                    "verifiedUsing": hash_id,
                    "software_fileKind": "file",
                },
                {
                    "type": "Hash",
                    "algorithm": "sha256",
                    "spdx:Core/hashValue": hash_val,
                    "@id": hash_id,
                },
            ]
            file_rel["to"].append(file_id)
        return pkg, pkg_id

    def run(self, edam, work_root):
        # with open(os.path.join(work_root, edam["name"] + ".debug.json"), "w") as f:
        #    f.write(json.dumps(edam))
        with open(os.path.join(work_root, edam["name"] + ".json"), "w") as f:
            ci_id = "https://FuseSoC/creationinfo/" + nanoid.generate()
            dt = datetime.datetime.now(datetime.UTC)
            dt.replace(microsecond=0)  # for isoformat to stop at seconds
            now = dt.isoformat()
            graph, sbom = self._generate_preamble(ci_id, now)

            core_dict = {}
            for fn in edam["files"]:
                core = fn["core"]
                name = fn["name"]
                if core in core_dict:
                    core_dict[core].append(name)
                else:
                    core_dict[core] = [name]
            for vlnv, flist in core_dict.items():
                license_expr = "No assertion"
                le = edam["cores"][vlnv]["license"]
                if le:
                    license_expr = le
                package, pid = self._generate_package(
                    work_root, ci_id, vlnv, license_expr, flist
                )
                graph += package
                if len(sbom["rootElement"]) < 1:
                    sbom["rootElement"] = pid
                else:
                    sbom["element"].append(pid)
            context = "https://spdx.github.io/spdx-spec/v3.0.1/rdf/spdx-context.jsonld"
            f.write(json.dumps({"@context": context, "@graph": graph}))
        return edam


def main():
    print("foo")


if __name__ == "__main__":
    main()
