#!/usr/bin/env python3
# Copyright(c) 2005, Thomas Matthijs <axxo@gentoo.org>
# Copyright(c) 2005, Gentoo Foundation
# Distributed under the terms of the GNU General Public Licence v2

import os
import sys
from optparse import OptionParser, make_option
from javatoolkit.cvv import CVVMagic


def main():
    options_list = [
        make_option(
            "-r",
            "--recurse",
            action="store_true",
            dest="deep",
            default=False,
            help="go into dirs"),
        make_option(
            "-t",
            "--target",
            type="string",
            dest="version",
            help="target version that is valid"),
        make_option(
            "-v",
            "--verbose",
            action="store_true",
            dest="verbose",
            default=False,
            help="Print version of every class"),
        make_option(
            "-s",
            "--silent",
            action="store_true",
            dest="silent",
            default=False,
            help="No output"),
        make_option(
            "-f",
            "--file-only",
            action="store_true",
            dest="file_only",
            default=False,
            help="Only output the files"),
    ]

    parser = OptionParser(
        "%prog -t version [-r] [-v] [-s] <class/jar files or dir>",
        options_list)
    (options, args) = parser.parse_args()

    if not options.version:
        print("-t is mandatory")
        sys.exit(2)

    options.version = int(options.version.split(".")[-1])

    cvv_magic = CVVMagic(options.version)

    for arg in args:
        if os.path.isfile(arg):
            cvv_magic.do_file(arg)

        if options.deep and os.path.isdir(arg):
            for root, dirs, files in os.walk(arg):
                for filename in files:
                    cvv_magic.do_file("%s/%s" % (root, filename))

    if options.file_only:
        lst = set([set[1] for set in cvv_magic.bad])
        for i in lst:
            print(i)
    else:
        if options.verbose:
            for set in cvv_magic.good:
                print("Good: %s %s %s" % set)

        if not options.silent:
            for set in cvv_magic.bad:
                print("Bad: %s %s %s" % set)

        print("CVV: %s\nChecked: %i Good: %i Bad: %i" %
              (options.version, len(cvv_magic.good) +
               len(cvv_magic.bad), len(cvv_magic.good), len(cvv_magic.bad)))

    if len(cvv_magic.bad) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
