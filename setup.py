import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="fusesoc",
    packages=["fusesoc", "fusesoc.capi1", "fusesoc.capi2", "fusesoc.provider"],
    use_scm_version={"relative_to": __file__, "write_to": "fusesoc/version.py",},
    author="Olof Kindgren",
    author_email="olof.kindgren@gmail.com",
    description=(
        "FuseSoC is a package manager and a set of build tools for HDL (Hardware Description Language) code."
    ),
    license="GPLv3",
    keywords=[
        "VHDL",
        "verilog",
        "hdl",
        "rtl",
        "synthesis",
        "FPGA",
        "simulation",
        "Xilinx",
        "Altera",
    ],
    url="https://github.com/olofk/fusesoc",
    long_description=read("README.rst"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points={"console_scripts": ["fusesoc = fusesoc.main:main"]},
    setup_requires=["setuptools_scm",],
    install_requires=[
        "edalize>=0.1.6",
        "ipyxact>=0.2.3",
        "pyparsing",
        "pyyaml",
        "simplesat>=0.8.0",
    ],
    # Supported Python versions: 2.7 or 3.5+
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4",
)
