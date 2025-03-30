#!/usr/bin/env python3
#
# Copyright 2008 James Le Cuirot <chewi@aura-online.co.uk>
# Copyright 2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#
# $Id$


import sys
import xml.etree.cElementTree as et


args = sys.argv[1:]
if len(args) == 0:
    args = ["build.xml"]


def main():
    for file in args:
        tree = et.ElementTree(file=file)
        tags = []

        for elem in tree.getiterator():
            for child in list(elem):
                if (
                    child.tag == "taskdef"
                    and child.get("classname") == "com.tonicsystems.jarjar.JarJarTask"
                ):
                    tags.append(child.get("name"))
                    elem.remove(child)

        for tag in tags:
            for jarjar in tree.getiterator(tag):
                if jarjar.get("destfile") or jarjar.get("jarfile"):
                    jarjar.tag = "jar"
                    if jarjar.get("verbose"):
                        del jarjar.attrib["verbose"]
                    for child in list(jarjar):
                        if (
                            child.tag == "keep"
                            or child.tag == "rule"
                            or child.tag == "zipfileset"
                        ):
                            jarjar.remove(child)

        with open(file, "w") as f:
            tree.write(f)


if __name__ == "__main__":
    main()
