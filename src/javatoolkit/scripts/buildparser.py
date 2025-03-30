#!/usr/bin/env python3
#
# Copyright(c) 2006, 2008 James Le Cuirot <chewi@aura-online.co.uk>
# Copyright(c) 2005, Karl Trygve Kalleberg <karltk@gentoo.org>
#
# Licensed under the GNU General Public License, v2
#
import os
import sys
from optparse import OptionParser

from ..parser.parser import Parser
from ..parser.buildproperties import BuildPropertiesParser
from ..parser.manifest import ManifestParser
from ..parser.tree import Node, ParseError

__author__ = [
    "James Le Cuirot <chewi@aura-online.co.uk>",
    "Karl Trygve Kalleberg <karltk@gentoo.org>",
]
__version__ = "0.3.0"
__productname__ = "buildparser"
__description__ = "A parser for build.properties and JAR manifest files."


def parse_args():
    usage = "buildparser [options] [node name] [replacement] <filename>"
    about = (
        __productname__
        + " : "
        + __description__
        + "\n"
        + "Version : "
        + __version__
        + "\n"
        "Authors : " + __author__[0]
    )

    for x in __author__[1:]:
        about += "\n          " + x

    parser = OptionParser(usage, version=about)

    parser.add_option(
        "-t",
        "--type",
        action="store",
        type="choice",
        dest="type",
        choices=["manifest", "buildprops"],
        help="Type of file to parse: manifest or buildprops",
    )

    parser.add_option(
        "-i",
        "--in-place",
        action="store_true",
        dest="in_place",
        help="Edit file in place when replacing",
    )

    parser.add_option(
        "-w",
        "--wrap",
        action="store_true",
        dest="wrap",
        help="Wrap when returning singular values",
    )

    opt, args = parser.parse_args()

    if len(args) > 3:
        parser.error("Too many arguments specified!")

    elif len(args) == 0:
        parser.error("A filename must be specified!")

    elif not os.path.isfile(args[-1]):
        parser.error(args[-1] + " does not exist!")

    return opt, args


def main():
    opt, args = parse_args()

    f = open(args[-1])

    t = Node()
    p = Parser()

    try:
        if opt.type == "manifest":
            p = ManifestParser()

        elif opt.type == "buildprops":
            p = BuildPropertiesParser()

        elif os.path.basename(f.name) == "MANIFEST.MF":
            p = ManifestParser()

        elif os.path.basename(f.name) == "build.properties":
            p = BuildPropertiesParser()

        else:
            sys.exit(
                __productname__
                + ": error: Unknown file type. Specify using the -t option."
            )

        t = p.parse(f)
        f.close()

    except ParseError:
        sys.exit(__productname__ + ": error: Unable to parse file.")

    if len(args) > 2:
        n = t.find_node(args[0])

        if n is not None:
            n.value = args[1]
        else:
            t.add_kid(Node(args[0], args[1]))

        if opt.in_place:
            f = open(args[-1], "w+")
            p.output(f, t)
            f.close()

        else:
            p.output(sys.stdout, t)

    elif len(args) > 1:
        n = t.find_node(args[0])

        if n is not None:
            if opt.wrap:
                print(p.wrapped_value(n))
            else:
                print(n.value)

    else:
        for x in t.node_names():
            print(x)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user, aborting.")
