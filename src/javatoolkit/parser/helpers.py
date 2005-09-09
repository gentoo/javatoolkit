#! /usr/bin/python2
#
# Copyright(c) 2005, James Le Cuirot <chewi@ffaura.com>
# Copyright(c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright(c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: /var/cvsroot/gentoo-src/javatoolkit/src/javatoolkit/parser/helpers.py,v 1.3 2004/11/08 19:31:51 karltk Exp $


def expand(root, expr, realroot = None):
	"""Evaluates a path expression on a given tree.
	
	@param root - the root of the tree
	@param expr - the expression to resolve
	
	@return the expanded string
	"""

	if realroot == None:
		realroot = root

	expanded = ""
	in_varref = False
	varname = ""
   
	for i in range(len(expr)):
		x = expr[i]

		if in_varref:

			if x == "}":
				in_varref = False
				expanded += expand(root, realroot.find_node(varname).value, realroot)
				varname = ""
			elif x != "{":
				varname += expr[i]

		elif x == "$" and i < len(expr) and expr[i + 1] == "{":
			in_varref = True

		else:
			expanded += x
   
	return expanded

def strip_varmarker(s):
	"""Strips away ${ and } in a variable expression. Idempotent if marker not found.
		
	Example: "${foo}" -> "foo"
	Example: "foo" -> "foo"
	"""
	
	if s.startswith("${") and s.endswith("}"):
		return s[2:-1]
	
	return s
	
if __name__ == "__main__":
	print "This is not an executable module"	