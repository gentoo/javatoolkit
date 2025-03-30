# Copyright(c) 2006, 2008, James Le Cuirot <chewi@aura-online.co.uk>
# Copyright(c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright(c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2

from .tree import *
from . import parser


class BuildPropertiesParser(parser.Parser):

    def parse(self, ins):
        """Parse an input stream containing an ant build.properties file. Return a
        structured document represented by tree.Node

        @param ins - input stream
        @return tree.Node containing the structured representation
        """

        lineno = 0
        continued_line = False
        inside_html_comment = False
        attrib = ""
        value = ""
        root = Node()

        for x in ins.readlines():
            lineno += 1
            x = x.strip()

            if inside_html_comment and x.find("-->") != -1:
                inside_html_comment = False
                x = x.split("-->", 1)[0]

            if x.find("<!--") != -1:
                inside_html_comment = True

            if inside_html_comment:
                continue

            if continued_line:
                continued_line = False
                value += x.strip('"')

                if len(value) and value[-1] == "\\":
                    value = value[:-1]
                    continued_line = True
                    continue

                root.add_kid(Node(attrib, value))
                continue

            if len(x) == 0 or x[:1] == "#":
                continue

            x = x.split("#", 1)[0]
            xs = x.split("=", 2)

            if len(xs) > 1:
                attrib = xs[0].strip()
                value = xs[1].strip().strip('"')

                if value != "" and value[-1] == "\\":
                    value = value[:-1]
                    continued_line = True
                    continue

                root.add_kid(Node(attrib, value))

            else:
                raise ParseError("Malformed line " + str(lineno))

        return root

    def output(self, ous, tree):
        tree.output(ous, "", " = ", "")

    def wrapped_value(self, node):
        return node.output_value()
