#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright 2004-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public Licence v2
# $Header: /var/cvsroot/gentoo-src/javatoolkit/src/bsfix/xml-rewrite.py,v 1.6 2005/07/19 10:35:18 axxo Exp $

# Author: Saleem Abdulrasool <compnerd@compnerd.org>
# Maintainer: Gentoo Java Herd <java@gentoo.org>
# Python based XML modifier

# ChangeLog
# Petteri Räty <betelgeuse@gentoo.org
#	   December 06, 2006 - Changed to use xml.parsers.expat and basically rewrote the whole file
# Saleem A. <compnerd@compnerd.org>
#	   December 23, 2004 - Initial Write
#	   December 24, 2004 - Added usage information

import sys
import StringIO

from xml.sax.saxutils import quoteattr,escape

from optparse import OptionParser, make_option

__version__ = "$Revision: 1.7 $"[11:-2]

class DomRewriter:
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

	def process(self,in_stream):
		from xml.dom.minidom import parse

		self.document = parse(in_stream);

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

class ExpatRewriter:

	def __init__(self, elems, attributes, values, index):
		self.buffer = StringIO.StringIO()
		self.p = self.buffer.write
		self.elems = elems
		self.attributes = attributes
		self.values = values

	def process(self, in_stream):
		from xml.parsers.expat import ParserCreate
		parser = ParserCreate()

		parser.StartElementHandler = self.start_element
		parser.EndElementHandler = self.end_element
		parser.CharacterDataHandler = self.char_data
		parser.ParseFile(in_stream)
		self.p('\n')

	def write(self, out_stream):
		out_stream.write(self.buffer.getvalue())
		self.buffer.close()
		self.buffer = StringIO.StringIO()
		self.p = self.buffer.write

	def write_attr(self,a,v):
		self.buffer.write('%s=%s ' % (a,quoteattr(v)))

	def start_element(self, name, attrs):
		self.p('<%s ' % name)

		match = ( name in self.elems )
		
		for a,v in attrs.iteritems():
			if not ( match and a in self.attributes ):
				self.write_attr(a,v)
		
		if match:
			for i, attr in enumerate(self.attributes):
				self.write_attr(attr, self.values[i])

		self.p('>')

	def end_element(self,name):
		self.p('</%s>' % name)

	def char_data(self,data):
		self.p(escape(data))

if __name__ == '__main__':
	usage = "XML Rewrite Python Module Version " + __version__ + "\n"
	usage += "Copyright 2004 Gentoo Foundation\n"
	usage += "Distributed under the terms of the GNU General Public Lincense v2\n"
	usage += "Please contact the Gentoo Java Herd <java@gentoo.org> with problems.\n"
	usage += "\n"
	usage += "Usage:\n"
	usage += "	xml-rewrite.py [-f file] --delete -e tag [-e tag] -a attribute [-a attribute] [-i index]\n"
	usage += "	xml-rewrite.py [-f file] --change -e tag [-e tag] -a attribute -v value [-a attribute -v value] [-i index]\n"
	usage += "\n"
	usage += "If the -f parameter is not utilized, the script will read and\n"
	usage += "write to stdin and stdout respectively.  The use of quotes on\n"
	usage += "parameters will break the script.\n"


	def error(message):
		print "ERROR: " + message
		sys.exit(1)


#	 if len(sys.argv) == 1:
#		 usage(True)

	options_list = [ 
		make_option ("-f", "--file", action="append", dest="files", help="Transform files instead of operating on stdout and stdin"),
		make_option ("-c", "--change", action="store_true", dest="doAdd", default=False, help="Change the value of an attribute.  If it does not exist, it will be created."),
		make_option ("-d", "--delete", action="store_true", dest="doDelete", default=False, help="Delete an attribute from matching elements."),
		make_option ("-e", "--element", action="append", dest="elements", help="Tag of the element of which the attributes to be changed.  These can be chained for multiple elements."),
		make_option ("-a", "--attribute", action="append", dest="attributes", help="Attribute of the matching elements to change. These can be chained for multiple value-attribute pairs"),
		make_option ("-v", "--value", action="append", dest="values", help="Value to set the attribute to."),
		make_option ("-i", "--index", type="int", dest="index", help="Index of the match.  If none is specified, the changes will be applied to all matches within the document. Starts from zero.")
	]

	parser = OptionParser(usage, options_list)
	(options, args) = parser.parse_args()


	# Invalid Arguments Must be smited!
	if not options.doAdd and not options.doDelete:
		print usage
		print
		error("No action was specified.")

	if options.doAdd and options.doDelete:
		error("Unable to perform multiple actions simultaneously.")

	if not options.elements or not options.attributes:
		error("At least one element and attribute must be specified.")

	if options.doAdd and not options.values:
		error("You must specify values for the attributes to be modified.")
	
	if options.doAdd and len(options.values) != len(options.attributes):
		error("You must give value for every attribute you are changing.")
	# End Invalid Arguments Check
	
	import codecs
	
	def get_rewriter(options):
		if options.index or options.doDelete:
			# java-ant-2.eclass does not use these options so we can optimize the ExpatWriter 
			# and let the DomRewriter do these. Also keeps the index option compatible for sure.
			rewriter = DomRewriter(options.elements, options.attributes, options.values, options.index)
			print "Using DOM to rewrite the build.xml files"
		else:
			rewriter = ExpatRewriter(options.elements, options.attributes, options.values, options.index)
			print "Using Expat to rewrite the build.xml files"

		return rewriter
	
	rewriter = get_rewriter(options)

	if options.files:
		for file in options.files:
			print "Rewriting %s" % file
			f = open(file,"r")
			rewriter.process(f)
			f.close()		
			f = open(file, "w")
			rewriter.write(codecs.getwriter('utf-8')(f))
			f.close()
	else:
		rewriter.process(sys.stdin)
		rewriter.write(codecs.getwriter('utf-8')(sys.stdout))

