#!/usr/bin/env python
"""JackCompiler.py: main script for the Jack language compiler

Compiles a Jack program directory, or a single Jack source file, to Hack VM
code.
"""
import argparse
import os
import sys

from compiler import Compiler


def main(args):
    inpath = args.inputpath
    outdir = args.outdir

    if os.path.isdir(inpath):
        # For an input directory, scan the directory for *.jack files, and
        # compile each such file into VM code as a .vm file in the output
        # directory and with the same base name as the input .jack file.
        if outdir is None:
            outdir = inpath
        with os.scandir(inpath) as entries:
            sources = [
                    os.path.join(inpath, x.name) for x in entries
                    if x.name.endswith('.jack') and x.is_file()]
    else:
        # For a single input file, compile that file and write the VM
        # code output to a file with the same base name but with a *.vm
        # suffix.
        if outdir is None:
            outdir = os.path.dirname(inpath)
        sources = [inpath]

    try:
        for source in sources:
            basename = os.path.basename(os.path.splitext(source)[0])
            outpath = os.path.join(outdir, f'{basename}.vm')
            sys.stdout.write(f"Compiling {source} -> {outpath}\n")
            with open(source, 'r') as infile:
                with open(outpath, 'w') as outfile:
                    comp = Compiler(infile, outfile)
                    comp.compile()

        return 0
    except Exception as e:
        sys.stderr.write(str(e))
        return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputpath')
    parser.add_argument('outdir', default=None)

    args = parser.parse_args()
    sys.exit(main(args))
