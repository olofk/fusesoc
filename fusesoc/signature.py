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
    Reads a given core file and returns the canonical (signed)
    part.
    """
    file = open(data_file_name, "rb")
    core_raw = file.read()
    file.close()
    if core_raw.startswith(b"CAPI=2:"):
        # Core file is single document, no built in signature.  We
        # sign everything after the header line.
        core_canonical = core_raw[7:].strip()
    else:
        # Core file is not a valid CAPI=2 document.
        raise RuntimeError("Signature file is not a valid CAPI=2 document.")
    return core_canonical


def sign(data_file_name, key_file_name, old_sig_file):
    """
    Read a core file, sign it, and return the signature yaml document as a string.
    """
    # Get the name and key type from the public key file, which we
    # assume is in the same directory and has the same name with .pub
    # appended.
    file = open(key_file_name + ".pub")
    key_parts = file.read().split(" ")
    file.close()
    key_type = key_parts[0].strip()
    signatory = key_parts[2].strip()
    core_canonical = read_core(data_file_name)
    cc_data = utils.yaml_read(core_canonical.decode("utf-8"))
    cmd = ["ssh-keygen", "-Y", "sign", "-f", key_file_name, "-n", "file"]
    logger.info("Run command: " + " ".join(cmd))
    res = subprocess.run(cmd, input=core_canonical, capture_output=True)
    sig_data = {
        "coresig": {
            "name": cc_data["name"],
            "signatures": [
                {
                    "type": key_type,
                    "user_id": signatory,
                    "signature": res.stdout.decode("utf-8").strip(),
                },
            ],
        }
    }

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

    The parameter trust_file_name must point to an ssh trust file
    which lists the users and public keys that are trusted, one per
    line, in the format:

        <user_name> <keytype> <public key>

    See man ssh-keygen for details.
    """
    logger.debug("verify core:       " + data_file_name)
    logger.debug("against signature: " + sig_file_name)
    logger.debug("with trustfile:    " + trust_file_name)
    core_canonical = read_core(data_file_name)
    core = utils.yaml_read(core_canonical.decode("utf-8"))
    sig_data = utils.yaml_fread(sig_file_name)
    if sig_data["coresig"]["name"] != core["name"]:
        raise RuntimeError(
            "Signature file and core file must have the same 'name' field."
        )
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
        logger.debug("Run command: " + str(cmd))
        res = subprocess.run(cmd, input=core_canonical, capture_output=True)
        # A user may have signed a core with several keys, report OK
        # as long as one of them matches.
        try:
            user_results[sig["user_id"]] |= res.returncode == 0
        except KeyError:
            user_results[sig["user_id"]] = res.returncode == 0
        os.remove(tmp_name)
    logger.debug("Result: " + str(user_results))
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
