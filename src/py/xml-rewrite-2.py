#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# vim: set ai ts=8 sts=0 sw=8 tw=0 noexpandtab:

# Copyright 2004-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public Licence v2

# Authors:
#	Saleem Abdulrasool <compnerd@compnerd.org>
#	Petteri Räty <betelgeuse@gentoo.org>
# Maintainer: Gentoo Java Herd <java@gentoo.org>
# Python based XML modifier

# ChangeLog
# Petteri Räty <betelgeuse@gentoo.org
#	   December 06, 2006 - Changed to use xml.parsers.expat and basically rewrote the whole file
#	   December 29, 2006 - Added a SAX based implementation to handle entities etc ( test on dev-java/skinlf )
# Saleem A. <compnerd@compnerd.org>
#	   December 23, 2004 - Initial Write
#	   December 24, 2004 - Added usage information


import sys
import io
from xml.sax.saxutils import quoteattr,escape
from optparse import OptionParser, make_option


__version__ = "$Revision: 1.7 $"[11:-2]


def add_gentoo_classpath(document):
	matches = document.getElementsByTagName("classpath")
	gcp = document.createElement("location")
	gcp.setAttribute("path","${gentoo.classpath}")

	handled_refs = set()
	for match in matches:
		if match.hasAttribute("refid"):
			refid = match.getAttribute("refid")
			for ref in document.getElementsByTagName("path"):
				id = ref.getAttribute("id")
				if id not in handled_refs and id == refid:
					gcp = document.createElement("pathelement")
					gcp.setAttribute("path","${gentoo.classpath}")
					ref.appendChild(gcp)
					handled_refs.add(id)
				else:
					match.appendChild(gcp)

class DomRewriter:
	"""
	The old DOM rewriter is still around for index based stuff. It can
	be used for all the complex stuff but portage needed features should
	be in StreamRewriterBase subclasses as they are much faster.
	"""
	from xml.dom import NotFoundErr

	def __init__(self, modifyElems, attributes, values=None, index=None):
		self.modify = modifyElems
		self.attributes = attributes
		self.values = values
		self.index = index

	def change_elem(self, elem):
		for i,attr in enumerate(self.attributes):
			if self.values:
				elem.setAttribute(attr, self.values[i])
			else:
				try:
					elem.removeAttribute(attr)
				except DomRewriter.NotFoundErr:
					continue

	def process(self,in_stream,callback=None):
		from xml.dom.minidom import parse

		self.document = parse(in_stream);

		if callback:
			callback(self.document)

		if not self.modify:
			return

		for tag in self.modify:
			matches = self.document.getElementsByTagName(tag)
			if matches:
				if self.index == None:
					for match in matches:
						self.change_elem(match)
				else:
					self.change_elem(matches[self.index])

	def write(self,stream):
		stream.write(self.document.toxml())

class StreamRewriterBase:
	def __init__(self, elems, attributes, values, index,
	      sourceElems = [], sourceAttributes = [], sourceValues = [],
	      targetElems = [], targetAttributes = [], targetValues = []  ):
		self.buffer = io.StringIO()
		self.__write = self.buffer.write
		self.elems = elems		or []
		self.attributes = attributes	or []
		self.values = values		or []
		self.sourceElems = sourceElems	or []
		self.sourceAttributes = sourceAttributes	or []
		self.sourceValues = sourceValues		or []
		self.targetElems = targetElems			or []
		self.targetAttributes = targetAttributes	or []
		self.targetValues = targetValues		or []

	def p(self,str):
		self.__write(str.encode('utf8'))

	def write(self, out_stream):
		value = self.buffer.getvalue()
		out_stream.write(value)
		self.buffer.truncate(0)

	def write_attr(self,a,v):
		self.p('%s=%s ' % (a,quoteattr(v, {'©':'&#169;'})))

	def start_element(self, name, attrs):
		self.p('<%s ' % name)

		match = ( name in self.elems )
		matchSource = ( name in self.sourceElems )
		matchTarget = ( name in self.targetElems )

		for a,v in attrs:
			if not (
				(match and a in self.attributes)
				or (matchSource and a in self.sourceAttributes)
				or (matchTarget and a in self.targetAttributes)
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

class ExpatRewriter(StreamRewriterBase):
	"""
	The only problem with this Expat based implementation is that it does not
	handle entities doctypes etc properly so for example dev-java/skinlf fails.
	"""
	def process(self, in_stream):
		from xml.parsers.expat import ParserCreate
		parser = ParserCreate()

		parser.StartElementHandler = self.start_element
		parser.EndElementHandler = self.end_element
		parser.CharacterDataHandler = self.char_data
		parser.ParseFile(in_stream)
		self.p('\n')

	def start_element(self, name, attrs):
		StreamRewriterBase(self, name, iter(attrs.items()))

	def end_element(self,name):
		self.p('</%s>' % name)

	def char_data(self,data):
		self.p(escape(data))

from xml.sax.saxutils import XMLGenerator
class SaxRewriter(XMLGenerator, StreamRewriterBase):
	"""
	Using Sax gives us the support for writing back doctypes and all easily
	and is only marginally slower than expat as it is just a tight layer over it
	"""
	def __init__(self, elems, attributes, values, index,
	      sourceElems = [], sourceAttributes = [], sourceValues = [],
	      targetElems = [], targetAttributes = [], targetValues = []):
		StreamRewriterBase.__init__(self, elems, attributes, values, index,
			      sourceElems, sourceAttributes, sourceValues,
			      targetElems, targetAttributes, targetValues)
		XMLGenerator.__init__(self, self.buffer, 'UTF-8')

	def process(self, in_stream):
		from xml.sax import parse
		parse(in_stream, self)
		self.p('\n')

	def startElement(self, name, attrs):
		self.start_element(name, list(attrs.items()))

def main():
    usage = "XML Rewrite Python Module Version " + __version__ + "\n"
    usage += "Copyright 2004,2006,2007 Gentoo Foundation\n"
    usage += "Distributed under the terms of the GNU General Public Lincense v2\n"
    usage += "Please contact the Gentoo Java Team <java@gentoo.org> with problems.\n"
    usage += "\n"
    usage += "Usage:\n"
    usage += "	xml-rewrite.py [-f file] --delete [-g] -e tag [-e tag] -a attribute [-a attribute] [-i index]\n"
    usage += "	xml-rewrite.py [-f file] --change [-g] -e tag [-e tag] -a attribute -v value [-a attribute -v value] \\\n"
    usage += "			[--source-element tag] [--source-attribute attribute --source-value value] \\\n"
    usage += "			[--target-element tag] [--target-attribute attribute --target-value value] [-i index]\n"
    usage += "Or:\n"
    usage += "	xml-rewrite.py [-f file] -g\n"
    usage += "\n"
    usage += "If the -f parameter is not utilized, the script will read and\n"
    usage += "write to stdin and stdout respectively.  The use of quotes on\n"
    usage += "parameters will break the script.\n"

    def error(message):
	print("ERROR: " + message)
	sys.exit(1)

#	if len(sys.argv) == 1:
#		usage(True)
    options_list = [
	make_option ("-f", "--file", action="append", dest="files", help="Transform files instead of operating on stdout and stdin"),
	make_option ("-g", "--gentoo-classpath", action="store_true", dest="gentoo_classpath", help="Rewrite build.xml to use gentoo.classpath where applicable."),
	make_option ("-c", "--change", action="store_true", dest="doAdd", default=False, help="Change the value of an attribute.  If it does not exist, it will be created."),
	make_option ("-d", "--delete", action="store_true", dest="doDelete", default=False, help="Delete an attribute from matching elements."),
	make_option ("-e", "--element", action="append", dest="elements", help="Tag of the element of which the attributes to be changed.  These can be chained for multiple elements."),
	make_option ("-a", "--attribute", action="append", dest="attributes", help="Attribute of the matching elements to change. These can be chained for multiple value-attribute pairs"),
	make_option ("-v", "--value", action="append", dest="values", help="Value to set the attribute to."),
	make_option ("-r", "--source-element", action="append", dest="source_elements", help="Tag of the element of which the attributes to be changed just in source scope.  These can be chained for multiple elements."),
	make_option ("-t","--source-attribute", action="append", dest="source_attributes", help="Attribute of the matching elements to change. These can be chained for multiple value-attribute pairs (for source only)"),
	make_option ("-y", "--source-value", action="append", dest="source_values", help="Value to set the attribute to. (sourceonly)"),
	make_option ("-j", "--target-element", action="append", dest="target_elements", help="Tag of the element of which the attributes to be changed just in target scope.  These can be chained for multiple elements."),
	make_option ("-k", "--target-attribute", action="append", dest="target_attributes", help="Attribute of the matching elements to change. These can be chained for multiple value-attribute pairs (for targetonly)"),
	make_option ("-l", "--target-value", action="append", dest="target_values", help="Value to set the attribute to (targeronly)."),
	make_option ("-i", "--index", type="int", dest="index", help="Index of the match.  If none is specified, the changes will be applied to all matches within the document. Starts from zero.")
    ]

    parser = OptionParser(usage, options_list)
    (options, args) = parser.parse_args()
	# Invalid Arguments Must be smited!
    if not options.doAdd and not options.doDelete and not options.gentoo_classpath:
	print(usage)
	print()
	error("No action was specified.")

    if not options.gentoo_classpath:
	if options.doAdd and options.doDelete:
	    error("Unable to perform multiple actions simultaneously.")
	if not options.elements and not options.target_elements and not options.source_elements:
	    error("At least one element (global, source only or target only) and attribute must be specified.")
	for elem in ( options.source_attributes or [] ):
	    if elem in ( options.attributes or [] ):
	        error("You can't set an attribute in global and source scope at the same time")
        for elem in ( options.target_attributes or [] ):
	    if elem in ( options.attributes or [] ):
	        error("You can't set an attribute in global and target scope at the same time")
	    if options.doAdd and (len(options.values or []) != len(options.attributes or [])
	    or len(options.source_values or [] ) != len(options.source_attributes or [])
	    or len(options.target_values or [] ) != len(options.target_attributes or [])):
		error("You must give attribute(s)/value(s) for every element you are changing.")

	# End Invalid Arguments Check

    def get_rewriter(options):
	if options.index or options.doDelete or options.gentoo_classpath:
		    # java-ant-2.eclass does not use these options so we can optimize the ExpatWriter
		# and let the DomRewriter do these. Also keeps the index option compatible for sure.
	    rewriter = DomRewriter(options.elements, options.attributes, options.values, options.index)
	else:
	    rewriter = SaxRewriter(options.elements, options.attributes, options.values, options.index,
			options.source_elements, options.source_attributes, options.source_values,
			options.target_elements, options.target_attributes, options.target_values)
	return rewriter

    rewriter = get_rewriter(options)

    if options.files:
	import os
	for file in options.files:
	    print("Rewriting %s" % file)
	    # First parse the file into memory
	    # Tricks with cwd are needed for relative includes of other xml files to build.xml files
	    cwd = os.getcwd()
	    dirname = os.path.dirname(file)
	    if dirname != '': # for file = build.xml comes out as ''
		os.chdir(os.path.dirname(file))
	    f = open(os.path.basename(file),"r")
	    if options.gentoo_classpath:
		rewriter.process(f,add_gentoo_classpath)
	    else:
		rewriter.process(f)
	    os.chdir(cwd)
	    f.close()
	    # Then write it back to the file
	    f = open(file, "w")
	    rewriter.write(f)
	    f.close()

    else:
	if options.gentoo_classpath:
	    rewriter.process(sys.stdin,add_gentoo_classpath)
	else:
	    rewriter.process(sys.stdin)
	rewriter.write(sys.stdout)


if __name__ == '__main__':
    main()
