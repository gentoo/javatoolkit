# Copyright(c) 2006, 2008, James Le Cuirot <chewi@aura-online.co.uk>
# Copyright(c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright(c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
import sys


class ParseError:
    def __init__(self, error):
        self.error = error


class NodeIter:
    def __init__(self, node):
        self._node = node
        self._index = 0

    def __next__(self):
        self._index += 1
        if self._index >= len(self._node._kids):
            raise StopIteration
        return self._node._kids[self._index]


class Node:
    def __init__(self, name=None, value=None):
        self.name = name
        self.value = value
        self._kids = []

    def __iter__(self):
        return NodeIter(self)

    def add_kid(self, kid):
        for x in self._kids:
            if x.name == kid.name:
                return

        self._kids.append(kid)

    def _dump_kids(self, ous, indent):
        for x in self._kids:
            x.dump(ous, indent + 1)

    """
    Dump self as text to stream.
    """

    def dump(self, ous, indent=0):
        if self.name:
            ous.write((" " * indent) + self.name + " = " + self.value + "\n")

        self._dump_kids(ous, indent)

    """
    Output self as text to stream using the given format.
    """

    def output(self, ous, before, between, after, wrap=None, indent=""):
        if self.name:
            ous.write(
                before
                + self.name
                + between
                + self.output_value(wrap, indent)
                + after
                + "\n"
            )

        for x in self._kids:
            x.output(ous, before, between, after, wrap, indent)

    """
    Return node value as string using the given format.
    """

    def output_value(self, wrap=None, indent=""):
        if wrap == None:
            return self.value
        else:
            return self.__wrap_outside_quotes(self.value, wrap, indent)

    """
    Returns a lists of all the node names.
    """

    def node_names(self):
        names = []

        if self.name:
            names.append(self.name)

        for x in self._kids:
            names.extend(x.node_names())

        return names

    """
    Find a given node name in a tree.

    @param tree - the tree to search in
    @param nodename - the name of the node to search for

    @return reference to the found node, if any
    """

    def find_node(self, nodename):
        if self.name == nodename:
            return self

        else:
            for x in self._kids:
                y = x.find_node(nodename)

                if y != None:
                    return y

        return None

    """
    Wrap using the given character and indent string, without wrapping
    inside quotes. Python's regexp engine cannot handle this.

    @param text - text to wrap
    @param wrap - character to wrap at
    @param indent - indent string to use, can be empty
    @param pos - recursive parameter only, don't use

    @return wrapped text
    """

    def __wrap_outside_quotes(self, text, wrap, indent, pos=None):
        if pos == None:
            pos = len(text)

        next_wrap = text.rfind(wrap, 0, pos)

        if next_wrap <= 0:
            return text

        num_quotes = text.count('"', next_wrap, pos)

        if num_quotes % 2 != 0:
            return self.__wrap_outside_quotes(
                text, wrap, indent, text.rfind('"', 0, next_wrap + 1)
            )

        return self.__wrap_outside_quotes(
            text[0:next_wrap] + wrap + "\n" + indent + text[next_wrap + 1 :],
            wrap,
            indent,
            next_wrap,
        )
