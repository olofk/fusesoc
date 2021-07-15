#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# This script uses the FuseSoc dependency builder to generate a list of files
# used for a particular target in a core file.  This can be used to auto-
# generate EDA style VC files without having to keep two sets of source file
# lists up to date.
# -----------------------------------------------------------------------------



import os, argparse, subprocess, logging
from pathlib import Path
from coregen import CoreDeps

logger = logging.getLogger(__name__)

header = """
// ----------------------------------------------------------------------
//            This file is auto-generated using core2vc.py.
//
//                  -=  D O   N O T   E D I T  =-
// ----------------------------------------------------------------------

+libext+.v+.sv+.svh

"""


def write_vc_file(deps, output_path):
    """Generate a VC file.

    The dependency tree has been built and we have a path to every file.
    Output a generic VC file that can be used by most EDA tools.
    """
    if not output_path:
        output_path = Path( deps.core.core_file.replace('.core', '.f') )
    logger.info("Generating VC file for core %s at %s" % (deps.toplevel, output_path))

    includes = ['', '// Include Directories']
    sources  = ['', '', '// Source Files']

    includes += [ '+incdir+%s' % d for d in deps.include_dirs ]
    sources  += [ '%s' % f for f in deps.source_files ]

    with output_path.open('w') as f:
        f.write(header)
        f.write('\n'.join(includes))
        f.write('\n'.join(sources))

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("system", help="Select a system to operate on")
    parser.add_argument("--cores-root",default=[],action="append", help="Specify the root directory to search")
    parser.add_argument("--target", help="Override default target")
    parser.add_argument("--tool", help="Override default tool for target")
    parser.add_argument("-f", "--flag", help="Define any user flags", default=[], action="append")
    parser.add_argument("-o", "--output-path", help="Override the default output path for the VC file")
    parser.add_argument("-v", "--verbose", action='store_true', help='Enable verbose logging')
    parser.add_argument("-l", "--log-file", help="Write log messages to file")
    args = parser.parse_args()
    return args


if __name__ == "__main__":

    args = parse_args()
    if not args:
        exit(0)

    if args.log_file:
        logging.basicConfig(filename=args.log_file, filemode='w', level=logging.DEBUG)

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=level)

    flags = { 'tool': args.tool, 'target': args.target }
    for flag in args.flag:
        if flag[0] == "+":
            flags[flag[1:]] = True
        elif flag[0] == "-":
            flags[flag[1:]] = False
        else:
            flags[flag] = True
    core_deps = CoreDeps( args.system, args.cores_root, flags )

    output_path = None
    if args.output_path is not None:
        output_path = Path(args.output_path)

    write_vc_file(core_deps, output_path)