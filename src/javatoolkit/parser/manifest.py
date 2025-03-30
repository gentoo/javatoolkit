# Copyright(c) 2006, 2008, James Le Cuirot <chewi@aura-online.co.uk>
# Licensed under the GNU General Public License, v2

from .tree import *
from . import parser


class ManifestParser(parser.Parser):

    def parse(self, ins):
        """Parse an input stream containing a MANIFEST.MF file. Return a
        structured document represented by tree.Node

        @param ins - input stream
        @return tree.Node containing the structured representation
        """

        lineno = 0
        attrib = ""
        value = ""
        root = Node()

        for x in ins.readlines():
            lineno += 1

            if len(x.strip()) == 0:
                continue

            if x[:1] == " ":
                if attrib == "":
                    raise ParseError("Malformed line " + str(lineno))

                value += x.strip()
                continue

            xs = x.split(": ", 2)

            if len(xs) > 1:
                if attrib != "":
                    root.add_kid(Node(attrib, value))

                attrib = xs[0]
                value = xs[1].strip()

            else:
                raise ParseError("Malformed line " + str(lineno))

        if attrib != "":
            root.add_kid(Node(attrib, value))

        return root

    def output(self, ous, tree):
        tree.output(ous, "", ": ", "", ",", " ")

    def wrapped_value(self, node):
        return node.output_value(",")
