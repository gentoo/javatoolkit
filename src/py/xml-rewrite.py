#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright 2004 Gentoo Foundation
# Distributed under the terms of the GNU General Public Licence v2
# $Header: /var/cvsroot/gentoo-src/javatoolkit/src/bsfix/xml-rewrite.py,v 1.6 2005/07/19 10:35:18 axxo Exp $

# Author: Saleem Abdulrasool <compnerd@compnerd.org>
# Maintainer: Gentoo Java Herd <java@gentoo.org>
# Python based XML modifier

# ChangeLog
# Saleem A. <compnerd@compnerd.org>
#      December 23, 2004 - Initial Write
#      December 24, 2004 - Added usage information


import sys
from xml.dom.minidom import parse
from optparse import OptionParser, make_option
from xml.dom import NotFoundErr


__version__ = "$Revision: 1.6 $"[11:-2]


class IOWrapper:
    def __init__(self, object):
        self.stream = object

    def stream(self):
        return self.stream

    def write(self, data):
        if self.stream == sys.stdin:
            sys.stdout.write(data.encode('utf-8'))
        else:
            file = open(self.stream, 'w')
            file.write(data.encode('utf-8'))
            file.close()


class Rewriter:
    def __init__(self, stream):
        self.stream = stream
        self.document = parse(stream.stream);

    def modifyAttribute(self, elementTag, attribute, value, index=None):
        matches = self.document.getElementsByTagName(elementTag)
        if matches:
            if index == None:
                for match in matches:
                    match.setAttribute(attribute, value)
            else:
                matches[index].setAttribute(attribute, value)

    def deleteAttribute(self, elementTag, attribute, index=None):
        matches = self.document.getElementsByTagName(elementTag)
        if matches:
            if index == None:
                for match in matches:
                    try:
                        match.removeAttribute(attribute)
                    except NotFoundErr:
                        continue
            else:
                try:
                    matches[index].removeAttribute(attribute)
                except NotFoundErr:
                    return

    def write(self):
        self.stream.write(self.document.toxml())


def main():
    usage = "XML Rewrite Python Module Version " + __version__ + "\n"
    usage += "Copyright 2004 Gentoo Foundation\n"
    usage += "Distributed under the terms of the GNU General Public Lincense v2\n"
    usage += "Please contact the Gentoo Java Herd <java@gentoo.org> with problems.\n"
    usage += "\n"
    usage += "Usage:\n"
    usage += "  xml-rewrite.py [-f] --delete -e tag [-e tag] -a attribute [-i index]\n"
    usage += "  xml-rewrite.py [-f] --change -e tag [-e tag] -a attribute -v value [-i index]\n"
    usage += "\n"
    usage += "If the -f parameter is not utilized, the script will read and\n"
    usage += "write to stdin and stdout respectively.  The use of quotes on\n"
    usage += "parameters will break the script.\n"


    def error(message):
        print("ERROR: " + message)
        sys.exit(1)


#    if len(sys.argv) == 1:
#        usage(True)

    options_list = [
        make_option ("-f", "--file", type="string", dest="file", help="Read input from file instead of stdin"),
        make_option ("-c", "--change", action="store_true", dest="doAdd", default=False, help="Change the value of an attribute.  If it does not exist, it will be created."),
        make_option ("-d", "--delete", action="store_true", dest="doDelete", default=False, help="Delete an attribute from matching elements."),
        make_option ("-e", "--element", action="append", dest="elements", help="Tag of the element of which the attributes to be changed.  These can be chained for multiple elements."),
        make_option ("-a", "--attribute", type="string", dest="attribute", help="Attribute of the matching elements to change."),
        make_option ("-v", "--value", type="string", dest="value", help="Value to set the attribute to."),
        make_option ("-i", "--index", type="int", dest="index", help="Index of the match.  If none is specified, the changes will be applied to all matches within the document.")
    ]

    parser = OptionParser(usage, options_list)
    (options, args) = parser.parse_args()

    # Invalid Arguments Must be smited!
    if not options.doAdd and not options.doDelete:
        print(usage)
        print()
        error("No action was specified.")

    if options.doAdd and options.doDelete:
        error("Unable to perform multiple actions simultaneously.")

    if not options.elements or not options.attribute:
        error("At least one element and attribute must be specified.")

    if options.doAdd and not options.value:
        error("You must specify values for the attributes to be modified.")
    # End Invalid Arguments Check

    if options.file:
        source = options.file
    else:
        source = sys.stdin

    rewriter = Rewriter(IOWrapper(source))

    if options.doDelete:
        for element in options.elements:
            rewriter.deleteAttribute(element, options.attribute, options.index)

    if options.doAdd:
        for element in options.elements:
            rewriter.modifyAttribute(element, options.attribute, options.value, options.index)

    rewriter.write()


if __name__ == '__main__':
    main()
