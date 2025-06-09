#!/usr/bin/env python
# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import base64
import logging
import os
import subprocess
import sys
import tempfile

import yaml

from fusesoc import utils

logger = logging.getLogger(__name__)


def read_core(data_file_name):
    """
    Reads a given core file and returns a tuple containing the
    canonical (signed) part and, if the core file is a multi part yaml
    file, the signature part.  If the core file is not a multi part
    yaml file, the second part of the tuple is None.
    """
    file = open(data_file_name, "rb")
    core_raw = file.read()
    file.close()
    if core_raw.startswith(b"CAPI=2:"):
        # Core file is single document, no built in signature.  We
        # sign everything after the header line.
        core_canonical = core_raw[7:].strip()
        sig_data = None
    else:
        # Core file is multi document.  We sign the middle part
        # (between the ---).
        crs = core_raw.split(b"\n---")
        core_canonical = crs[1].strip()
        if len(crs) > 1:
            sig_data = crs[2]
        else:
            sig_data = None
    return core_canonical, sig_data


def sign(data_file_name, key_file_name, old_sig_file):
    """
    Read a core file, sign it, and return the signature yaml document as a string.

    The new signature will be added to any existing signatures, taken
    either from the core file, if it is a multi part yaml document and
    does _not_ begin with "CAPI=2:", or (overriding any signatures in
    the core file) from old_sig_file (unless it is None).
    """
    # Get the name and key type from the public key file, which we
    # assume is in the same directory and has the same name with .pub
    # appended.
    file = open(key_file_name + ".pub")
    key_parts = file.read().split(" ")
    file.close()
    key_type = key_parts[0].strip()
    signatory = key_parts[2].strip()
    core_canonical, old_sig = read_core(data_file_name)
    cc_data = utils.yaml_read(core_canonical.decode("utf-8"))
    cmd = ["ssh-keygen", "-Y", "sign", "-f", key_file_name, "-n", "file"]
    logger.info("Run command: " + " ".join(cmd))
    res = subprocess.run(cmd, input=core_canonical, capture_output=True)
    if old_sig_file:
        sig_data = utils.yaml_fread(old_sig_file)
        if sig_data["coresig"]["name"] != cc_data["name"]:
            raise RuntimeError(
                "Signature file and core file must have the same 'name' field."
            )
    elif old_sig:
        sig_data = utils.yaml_read(old_sig)
    else:
        sig_data = {
            "coresig": {
                "name": cc_data["name"],
                "signatures": [],
            }
        }
    sig_data["coresig"]["signatures"].append(
        {
            "type": key_type,
            "user_id": signatory,
            "signature": res.stdout.decode("utf-8").strip(),
        }
    )

    # Dump multi line signature in yaml | style.
    def str_presenter(dumper, data):
        if len(data.splitlines()) > 1:  # check for multiline string
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    yaml.add_representer(str, str_presenter)
    return yaml.dump(sig_data)


def verify(data_file_name, trust_file_name, sig_file_name):
    """
    Verify signatures of a core file and return a dictionary of
    users whos signatures were tried and their result (True or False).

    The signatures are taken from the yaml signature file
    sig_file_name, unless it is None, in which case data_file_name
    must be a multi part yaml document not beginning with "CAPI=2:"
    and have the yaml signature document as its second part.

    The parameter trust_file_name must point to an ssh trust file
    which lists the users and public keys that are trusted, one per
    line, in the format:

        <user_name> <keytype> <public key>

    See man ssh-keygen for details.

    If a user has signed the core file with several keys, as long as
    one of the signatures is correct, and that key is listed for that
    user in the trust file, that user_name will map to True in the
    returned dictionary.

    """
    core_canonical, old_sig = read_core(data_file_name)
    core = utils.yaml_read(core_canonical.decode("utf-8"))
    if sig_file_name:
        # If sig file provided, override sigs in core file.
        sig_data = utils.yaml_fread(sig_file_name)
        if sig_data["coresig"]["name"] != core["name"]:
            raise RuntimeError(
                "Signature file and core file must have the same 'name' field."
            )
    else:
        sig_data = utils.yaml_read(old_sig)
    user_results = {}
    for sig in sig_data["coresig"]["signatures"]:
        f_os, tmp_name = tempfile.mkstemp(prefix="sig_", suffix=".asc")
        os.write(f_os, bytes(sig["signature"].encode("utf-8")))
        os.close(f_os)
        cmd = [
            "ssh-keygen",
            "-Y",
            "verify",
            "-f",
            trust_file_name,
            "-I",
            sig["user_id"],
            "-n",
            "file",
            "-s",
            tmp_name,
        ]
        logger.info("Run command: " + str(cmd))
        res = subprocess.run(cmd, input=core_canonical, capture_output=True)
        try:
            user_results[sig["user_id"]] |= res.returncode == 0
        except KeyError:
            user_results[sig["user_id"]] = res.returncode == 0
        os.remove(tmp_name)
    return user_results


def main():
    logging.basicConfig(filename="pysig.log", level=logging.INFO)
    logger.info("Command line arguments: " + str(sys.argv))
    if (len(sys.argv) >= 4) and (sys.argv[1] == "sign"):
        dataf = sys.argv[2]
        keyf = sys.argv[3]
        if len(sys.argv) == 5:
            old_sig_file = sys.argv[4]
        else:
            old_sig_file = None
        sig = sign(dataf, keyf, old_sig_file)
        print(sig)

    if (len(sys.argv) >= 4) and (sys.argv[1] == "verify"):
        dataf = sys.argv[2]
        trustf = sys.argv[3]
        if len(sys.argv) == 5:
            sigf = sys.argv[4]
        else:
            sigf = None
        res = verify(dataf, trustf, sigf)
        print(res)


if __name__ == "__main__":
    main()
