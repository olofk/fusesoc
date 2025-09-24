#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import argparse
import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import warnings
from pathlib import Path

import argcomplete
import requests

from fusesoc import signature


def guess_provider():
    guess = {"found": False}
    cmd = ["git", "remote", "-v"]
    res = subprocess.run(cmd, capture_output=True).stdout.decode("utf-8").strip()
    lines = res.splitlines()
    if len(lines) < 1:
        return guess
    fetchlines = list(filter(lambda s: s.endswith("(fetch)"), lines))
    if len(fetchlines) < 1:
        return guess
    comps = fetchlines[0].split("/")
    if comps[2] == "github.com":
        guess["name"] = "github"
    else:
        guess["name"] = comps[2]
    user = comps[3]
    repo = comps[4]
    repo = repo[: len(repo) - len("(fetch)")].strip()
    cmd = ["git", "log", "-n", "1"]
    res = (
        subprocess.run(cmd, capture_output=True)
        .stdout.decode("utf-8")
        .strip()
        .splitlines()[0]
    )
    comps = res.split(" ")
    if (len(comps) >= 2) and (comps[0] == "commit"):
        version = comps[1]
    else:
        version = ""
    guess[
        "yaml"
    ] = """provider:
  name : {}
  user : {}
  repo : {}
  version : {}
""".format(
        guess["name"], user, repo, version
    )
    guess["found"] = True
    return guess


def core_publish(fs, args):
    core = _get_core(fs, args.core)
    uri = fs.config.publish_uri
    pem = fs.config.publish_uri_pem
    sigfile = core.core_file + ".sig"
    if (core.provider != None) and (core.provider.name != "github"):
        print(
            'The provider for this core is "'
            + core.provider.name
            + '" and only "github" is supported for publishing.  Aborting.'
        )
        return False
    if core.provider == None:
        provider_info = guess_provider()
        if provider_info["found"] == False:
            print(
                "No provider is given in core file or guessable from current project, and a provider of type github is needed for publishing.  Aborting."
            )
            return False
        if provider_info["name"] != "github":
            print(
                "No provider is given in core file, and the current project appears to not be on github, which is needed for publishing.  Aborting."
            )
            return False
        print(
            "No provider is given in core file, but the current project seems to be on github."
        )
        if not args.autoprovider:
            print(
                "The following provider section can be added to the core file if the --autoprovider flag is given to this command."
            )
            print(provider_info["yaml"])
            return False
        print("Adding the following provider section to the core file.")
        print(provider_info["yaml"])
        cf = open(core.core_file, "ab")
        cf.write(("\n" + provider_info["yaml"] + "\n").encode("utf-8"))
        cf.close()
        print("Now retry publishing.")
        return False

    print("Core provider: " + core.provider.name)
    print("Publish core file: " + core.core_file)
    fob_core = open(core.core_file, "rb")
    body = {"core_file": fob_core}
    fob_sig = None
    if os.path.exists(sigfile):
        print("and signature file: " + sigfile)
        fob_sig = open(sigfile, "rb")
        body["signature_file"] = fob_sig
    else:
        print("(without signature file)")
        sf_data = None
    if pem:
        print("with certificate from: " + pem)
    print("to api at: " + uri)
    if args.yes:
        print("without confirmation")
    else:
        c = input("Confirm by typing 'yes': ")
        if c != "yes":
            print("Aborted.")
            return False

    target = uri + "/v1/publish/"
    logger.debug("POST to " + target)
    res = requests.post(target, files=body, allow_redirects=True, verify=pem)
    if not res.ok:
        print("Request returned http result", res.status_code, res.reason)
        err = json.loads(res.content)
        print(json.dumps(err, indent=4))
    res.close()
    fob_core.close()
    if fob_sig:
        fob_sig.close()
