# -*- coding: UTF-8 -*-
# Copyright 2004-2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from xml.dom import NotFoundErr

class DomRewriter:
    """
    The old DOM rewriter is still around for index based stuff. It can
    be used for all the complex stuff but portage needed features should
    be in StreamRewriterBase subclasses as they are much faster.
    """
    def __init__(self, modifyElems = None, attributes = None , values=None, index=None):
        self.modifyElems = modifyElems
        self.attributes = attributes
        self.values = values
        self.index = index


    def delete_elements(self, document, **kwargs):
        if not self.modifyElems:
            return

        tomodify = []
        for tag in self.modifyElems:
            matches = document.getElementsByTagName(tag)
            if matches:
                if self.index == None:
                    for match in matches:
                        tomodify.append(match)
                else:
                    tomodify.append(matches[self.index])

        for elem in tomodify:
            for i,attr in enumerate(self.attributes):
                if self.values:
                    elem.setAttribute(attr, self.values[i])
                else:
                    try:
                        elem.removeAttribute(attr)
                    except DomRewriter.NotFoundErr:
                        continue


    def add_gentoo_classpath(self,document,**kwargs):
        if 'classpath' not in kwargs or not kwargs['classpath']:
            return

        cp = document.createElement("classpath")
        cp.setAttribute("path", kwargs['classpath'])
        last_parent = None

        # Add our classpath element to every node already containing a classpath element.
        for match in document.getElementsByTagName("classpath"):
            if last_parent != match.parentNode:
                match.parentNode.appendChild(cp.cloneNode(True))
                last_parent = match.parentNode

        # Add our classpath element to every javac node we missed earlier.
        for match in document.getElementsByTagName("javac") + document.getElementsByTagName("xjavac"):
            if not match.getElementsByTagName("classpath"):
                match.appendChild(cp.cloneNode(True))


    def process(self,in_stream,callback=None,*args,**kwargs):
        from xml.dom import minidom
        self.document = minidom.parseString(in_stream);

        if callback:
            callback(self.document,*args,**kwargs)


    def write(self,stream):
        stream.write(self.document.toxml("utf-8"))

# vim: set expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap:
