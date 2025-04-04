#!/usr/bin/env python3
#
# Copyright (c) Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright (c) Fabio Lessa <flessa@gmail.com>
# Copyright (c) 2005, Gentoo Foundation
#
# Python rewrite from the bash findclass initially performed
# by Fabio.
#
# Licensed under the GNU General Public License, v2.
#

import os
import re
import sys
import glob
from optparse import OptionParser
from subprocess import getstatusoutput
from java_config.jc_util import find_exec, collect_packages


__author__ = (
    "Karl Trygve Kalleberg <karltk@gentoo.org> and Fabio Lessa <flessa@gmail.com>"
)
__version__ = "0.1.0"
__productname__ = "findclass"
__description__ = "Gentoo Java Class Query Tool"


def parse_args():
    usage = "findclass [options] class.or.package.Name"
    about = (
        __productname__
        + " : "
        + __description__
        + "\n"
        + "Authors : "
        + __author__
        + "Version : "
        + __version__
    )

    parser = OptionParser(usage, version=about)
    parser.add_option(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="generate verbose output",
    )
    opt, files = parser.parse_args()

    if len(files) < 1:
        parser.error("Must supply at least one class or package name")

    return opt, files


def main():
    opt, files = parse_args()

    jarcmd = find_exec("jar")

    javapaths = [f.replace(".", "/") for f in files]
    matchers = [re.compile(p) for p in javapaths]

    for pkg in get_all_packages():
        if opt.verbose:
            print("Searching package %s" % pkg)
        for jar in collect_packages(pkg).split(":"):
            if opt.verbose:
                print("Searching jar %s" % jar)
            status, out = getstatusoutput("%s tvf %s" % (jarcmd, jar))
            for m in matchers:
                if m.search(out):
                    if opt.verbose:
                        print("Found in %s" % pkg, end=" ")
                    print(jar)


def get_all_packages():
    pkg = glob.glob("/usr/share/*/package.env")
    pkg = [os.path.basename(os.path.dirname(i)) for i in pkg]

    classpath = glob.glob("/usr/share/*/classpath.env")
    classpath = [os.path.basename(os.path.dirname(i)) for i in classpath]

    dir = glob.glob("/usr/share/java/packages/*")
    dir = [os.path.basename(i) for i in dir]

    pkg.extend(classpath)
    pkg.extend(dir)
    return pkg


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user, aborting.")
