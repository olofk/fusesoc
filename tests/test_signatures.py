# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import shutil
from pathlib import Path

import pytest
from test_common import tests_dir

from fusesoc import signature
from fusesoc.capi2.coreparser import Core2Parser
from fusesoc.core import Core

cores_root = os.path.join(tests_dir, "cores")
trustfiles_root = os.path.join(tests_dir, "signature_files", "trustfiles")
keyfiles_root = os.path.join(tests_dir, "signature_files", "keyfiles")
sigfile_root = os.path.join(tests_dir, "signature_files")


@pytest.fixture(scope="session", autouse=True)
def fix_key_premissions(request):
    """
    Private key files must be readable only to owner, or
    ssh-keygen will freak out, but git does not preserve permissions
    other than x, so we chmod all private test keys here.
    """
    priv_keys = [
        "user1_ecdsa",
        "user1_ed25519",
        "user1_rsa",
        "user2_ed25519",
        "user3_ed25519",
    ]
    for x in priv_keys:
        os.chmod(os.path.join(keyfiles_root, x), 0o600)


def test_signature_single_standalone():
    """
    Test signing and verifying a core as a single signature in a
    standalone file.
    """
    kf_ok = os.path.join(keyfiles_root, "user1_rsa")
    kf_bad = os.path.join(keyfiles_root, "user1_ecdsa")
    cf_ok = Core(Core2Parser(), os.path.join(cores_root, "sockit/sockit.core"))
    cf_bad = Core(Core2Parser(), os.path.join(cores_root, "misc/ghdltest.core"))
    sf_ok = os.path.join(sigfile_root, "sockit.sig")
    sf_bad1 = os.path.join(sigfile_root, "sockit_bad1.sig")
    sf_bad2 = os.path.join(sigfile_root, "sockit_bad2.sig")
    tf_ok1 = os.path.join(trustfiles_root, "trustfile_1rsa_and_2")
    tf_ok2 = os.path.join(trustfiles_root, "trustfile_1rsa+ed_and_3")
    tf_bad = os.path.join(trustfiles_root, "trustfile_1ed_and_2")

    to_sign = [
        {
            "key": kf_ok,
            "core": cf_ok,
            "sig": sf_ok,
        },
        {
            "key": kf_bad,
            "core": cf_ok,
            "sig": sf_bad1,
        },
        {
            "key": kf_ok,
            "core": cf_bad,
            "sig": sf_bad2,
        },
    ]
    for x in to_sign:
        sig = signature.sign(x["core"], x["key"], None)
        file = open(x["sig"], "w")
        file.write(sig)
        file.close()

    to_verify = [
        {
            "tf": tf_ok1,
            "core": cf_ok,
            "sig": sf_ok,
            "exception": False,
            "res": True,
        },
        {
            "tf": tf_ok2,
            "core": cf_ok,
            "sig": sf_ok,
            "exception": False,
            "res": True,
        },
        {
            "tf": tf_bad,
            "core": cf_ok,
            "sig": sf_ok,
            "exception": False,
            "res": False,
        },
        {
            "tf": tf_ok1,
            "core": cf_bad,
            "sig": sf_ok,
            "exception": True,
            "res": False,
        },
        {
            "tf": tf_ok2,
            "core": cf_bad,
            "sig": sf_ok,
            "exception": True,
            "res": False,
        },
        {
            "tf": tf_ok1,
            "core": cf_ok,
            "sig": sf_bad1,
            "exception": False,
            "res": False,
        },
        {
            "tf": tf_ok1,
            "core": cf_ok,
            "sig": sf_bad2,
            "exception": True,
            "res": False,
        },
        {
            "tf": tf_ok2,
            "core": cf_ok,
            "sig": sf_bad1,
            "exception": False,
            "res": False,
        },
        {
            "tf": tf_ok2,
            "core": cf_ok,
            "sig": sf_bad2,
            "exception": True,
            "res": False,
        },
        {
            "tf": tf_bad,
            "core": cf_bad,
            "sig": sf_ok,
            "exception": True,
            "res": False,
        },
    ]
    for x in to_verify:
        try:
            res = signature.verify(x["core"], x["tf"], x["sig"])
            e = False
        except RuntimeError:
            e = True
        assert e == x["exception"]
        if not e:
            assert len(res) == 1
            assert list(res.values())[0] == x["res"]
    os.remove(sf_ok)
    os.remove(sf_bad1)
    os.remove(sf_bad2)
