#!/usr/bin/env python3
#
# Copyright(c) 2005, Thomas Matthijs <axxo@gentoo.org>
# Copyright(c) 2005, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Id$

import os,sys
from optparse import OptionParser, make_option
from javatoolkit.cvv import *

def main():
    options_list = [
        make_option ("-r", "--recurse", action="store_true", dest="deep", default=False, help="go into dirs"),
        make_option ("-t", "--target", type="string", dest="version", help="target version that is valid"),
        make_option ("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Print version of every calss"),
        make_option ("-s", "--silent", action="store_true", dest="silent", default=False, help="No output"),
        make_option ("-f", "--file-only", action="store_true", dest="file_only", default=False, help="Only output the files"),
    ]

    parser = OptionParser("%prog -t version [-r] [-v] [-s] <class/jar files or dir>", options_list)
    (options, args) = parser.parse_args()

    if not options.version:
        print("-t is mandatory")
        sys.exit(2)

    options.version = int(options.version.split(".")[-1])

    cvv = cvv(options.version)

    for arg in args:
        if os.path.isfile(arg):
            cvv.do_file(arg)

        if options.deep and os.path.isdir(arg):
            for root, dirs, files in os.walk(arg):
                for filename in files:
                    cvv.do_file("%s/%s" % (root, filename))

    if options.file_only:
        lst = set([set[1] for set in cvv.bad])
        for i in lst:
            print(i)
    else:
        if options.verbose:
            for set in cvv.good:
                print("Good: %s %s %s" % set)

        if not options.silent:
            for set in cvv.bad:
                print("Bad: %s %s %s" % set)

        print("CVV: %s\nChecked: %i Good: %i Bad: %i" % (options.version, len(cvv.good)+len(cvv.bad) , len(cvv.good), len(cvv.bad)))

    if len(cvv.bad) > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
