#!/usr/bin/env python3

import sys, os
import xml.etree.cElementTree as et
from optparse import OptionParser


def main():
    parser = OptionParser()
    parser.add_option(
        '-c',
        '--changeattributes',
        dest='change',
        action="append",
        nargs=3)
    parser.add_option(
        '-g',
        '--gentooclasspath',
        dest="gcp",
        action="store_true",
        default=False)
    parser.add_option('-e', '--encoding', dest="encoding")
    (options, args) = parser.parse_args()

    changes = []
    if options.change:
        for c in options.change:
            changes.append((c[0].split(), c[1], c[2]))

    gcp = options.gcp
    gcp_str = '${gentoo.classpath}'
    gcp_sub = et.Element('classpath', path=gcp_str)

    for file in args:
        if os.path.getsize(file) == 0 : continue
        tree = et.ElementTree(file=file)
        if gcp or options.encoding:
            for javac in tree.iter('javac'):
                if gcp:
                    javac.attrib['classpath'] = gcp_str
                if options.encoding:
                    javac.attrib['encoding'] = options.encoding
                for javadoc in tree.iter('javadoc'):
                    if gcp:
                        javadoc.attrib['classpath'] = gcp_str
                        if options.encoding:
                            javadoc.attrib['encoding'] = options.encoding
        for c in changes:
            elems, attr, value = c
            for elem in elems:
                for e in tree.iter(elem):
                    e.attrib[attr] = value
        for junit in tree.iter('junit'):
            if gcp:
                junit.append(gcp_sub)
                junit.attrib['haltonfailure'] = 'true'

        with open(file, 'wb') as f:
            tree.write(f)


if __name__ == '__main__':
    main()
