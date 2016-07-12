import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "fusesoc",
    packages=['fusesoc',
              'fusesoc.build',
              'fusesoc.ipyxact',
              'fusesoc.simulator',
              'fusesoc.provider'],
    version = "1.5",
    author = "Olof Kindgren",
    author_email = "olof.kindgren@gmail.com",
    description = ("FuseSoC is a package manager and a set of build tools for HDL (Hardware Description Language) code."),
    license = "GPLv3",
    keywords = ["VHDL", "verilog", "hdl", "rtl", "synthesis", "FPGA", "simulation", "Xilinx", "Altera"],
    url = "https://github.com/olofk/fusesoc",
    long_description=read('readme.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points={
        'console_scripts': [
            'fusesoc = fusesoc.main:main'
        ]
    },
    install_requires=[
          'pyyaml',
    ],
)
