# -*- coding: UTF-8 -*-

# Copyright 2004-2005 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

import os
import sys
import io

from xml.sax.saxutils import XMLGenerator
from xml.sax.saxutils import quoteattr

class SaxRewriter(XMLGenerator):
    """
    Using Sax gives us the support for writing back doctypes and all easily
    and is only marginally slower than expat as it is just a tight layer over it
    """
    def __init__(self, **kwds):
        self.elems = 'elems' in kwds and kwds['elems'] or []
        self.attributes = 'attributes' in kwds and kwds['attributes'] or []
        self.values = 'values' in kwds and kwds['values'] or []
        self.sourceElems = 'sourceElems' in kwds and kwds['sourceElems'] or []
        self.sourceAttributes = 'sourceAttributes' in kwds and kwds['sourceAttributes'] or []
        self.sourceValues = 'sourceValues' in kwds and kwds['sourceValues'] or []
        self.targetElems = 'targetElems' in kwds and kwds['targetElems'] or []
        self.targetAttributes = 'targetAttributes' in kwds and kwds['targetAttributes'] or []
        self.targetValues = 'targetValues' in kwds and kwds['targetValues'] or []

        self.deleteElems = 'deleteElems' in kwds and kwds['deleteElems'] or []
        self.deleteAttributes = 'deleteAttributes' in kwds and kwds['deleteAttributes'] or []

        self.src_dirs = 'src_dirs' in kwds and kwds['src_dirs'] or []
        self.output_dir = 'output_dir' in kwds and kwds['output_dir'] or None

        self.buffer = io.StringIO()

        XMLGenerator.__init__(self, self.buffer, 'UTF-8')


    def add_gentoo_javadoc(self, name, attrs):
        self.p('<%s ' % name)
        for a,v in list(attrs.items()):
            self.write_attr(a,v)

        self.p('>')

        if name == "project":
            javadoc_str = """
            <target name=\"gentoojavadoc\" >
            <mkdir dir=\"""" + self.output_dir + """\" />
            <javadoc
            destdir=\"""" + self.output_dir + """\"
            author="true"
            version="true"
            use="true"
            windowtitle="javadoc">
            """

            for src_dir in self.src_dirs:
                javadoc_str += """
                <fileset dir=\"""" + src_dir + """\"    defaultexcludes="yes">
                <include name="**/*.java"/>
                </fileset>
                """

            javadoc_str += """
            </javadoc>
            </target>
            """

            self.p('%s' % javadoc_str)


    # write as they are or delete if wanted attributes first
    # next, add / update
    def modify_elements(self, name, attrs):
        self.p('<%s ' % name)

        match = ( name in self.elems )
        matchSource = ( name in self.sourceElems )
        matchTarget = ( name in self.targetElems )
        matchDelete = ( name in self.deleteElems )

        for a,v in list(attrs.items()):
            if not (
                (match and a in self.attributes)
                or (matchSource and a in self.sourceAttributes)
                or (matchTarget and a in self.targetAttributes)
                or (matchDelete and a in self.deleteAttributes)
            ):
                self.write_attr(a,v)

        if matchSource:
            for i, attr in enumerate(self.sourceAttributes):
                self.write_attr(attr, self.sourceValues[i])

        if matchTarget:
            for i, attr in enumerate(self.targetAttributes):
                self.write_attr(attr, self.targetValues[i])

        if match:
            for i, attr in enumerate(self.attributes):
                self.write_attr(attr, self.values[i])

        self.p('>')


    def char_data(self, data):
        self.p(escape(data))


    def write(self, out_stream):
        value = self.buffer.getvalue()
        out_stream.write(value)
        self.buffer.truncate(0)


    def p(self,str):
        self.buffer.write(str.encode('utf8'))


    def write_attr(self,a,v):
        self.p('%s=%s ' % (a,quoteattr(v, {'©':'&#169;'})))


    def process(self, in_stream, callback):
        self.startElement = callback
        from xml.sax import parseString
        parseString(in_stream, self)
        self.p('\n')

# vim: set expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap:
