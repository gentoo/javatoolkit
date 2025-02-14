#!/usr/bin/env python3
# Copyright 2004-2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public Licence v2


import os
import sys
import io
from optparse import OptionParser, make_option
from ..xml.DomRewriter import DomRewriter
from ..xml.SaxRewriter import SaxRewriter


def main():
    usage = """Copyright 2004, 2006, 2007, 2017 Gentoo Foundation
Distributed under the terms of the GNU General Public Licence v2

Reach out to the Gentoo Java Team <java@gentoo.org> for questions/problems.

Usage:
    xml-rewrite-3.py [-f file] --delete [-g] -n tag [-n tag] -m attribute [-m attribute] [-i index]
    xml-rewrite-3.py [-f file] --change [-g] -e tag [-e tag] -a attribute -v value [-a attribute -v value]
    xml-rewrite-3.py [-f file] --javadoc --source-directory dir [--source-directory dir2] --output-directory dir3
    xml-rewrite-3.py [-f file] --maven-cleaning
    xml-rewrite-3.py [-f file] -g

Additional parameters:
    [--source-element tag] [--source-attribute attribute --source-value value]
    [--target-element tag] [--target-attribute attribute --target-value value] [-i index]

Multiple actions can be done simultaneously.

If the -f parameter is not used, the script will read and
write to stdin and stdout respectively. The use of quotes on
parameters will break the script."""

    def error(message):
        print("ERROR: " + message)
        sys.exit(1)

    # instream is a string
    def doRewrite(rewriter, in_stream, callback=None, **kwargs):
        if callback:
            rewriter.process(in_stream, callback, **kwargs)
        else:
            rewriter.process(in_stream, **kwargs)

        out = io.StringIO()
        rewriter.write(out)
        return out.getvalue()

    def processActions(options, f):
        out_stream = f.read()
        newcp = "${gentoo.classpath}"
        if options.gentoo_classpath:
            rewriter = DomRewriter(
                options.elements,
                options.attributes,
                options.values,
                options.index)
            out_stream = doRewrite(
                rewriter,
                out_stream,
                rewriter.add_gentoo_classpath,
                classpath=newcp)

        if options.doJavadoc:
            rewriter = SaxRewriter(
                src_dirs=options.src_dirs,
                output_dir=options.javadoc_dir[0])
            out_stream = doRewrite(
                rewriter, out_stream, rewriter.add_gentoo_javadoc)

        if options.doAdd or options.doDelete:
            # java-ant-2.eclass does not use these options so we can optimize the ExpatWriter
            # and let the DomRewriter do these. Also keeps the index option
            # compatible for sure.
            if options.index:
                rewriter = DomRewriter(
                    options.delete_elements,
                    options.delete_attributes,
                    options.values,
                    options.index)
                out_stream = doRewrite(
                    rewriter, out_stream, rewriter.delete_elements)
            else:
                rewriter = SaxRewriter(
                    elems=options.elements,
                    attributes=options.attributes,
                    values=options.values,
                    sourceElems=options.source_elements,
                    sourceAttributes=options.source_attributes,
                    sourceValues=options.source_values,
                    targetElems=options.target_elements,
                    targetAttributes=options.target_attributes,
                    targetValues=options.target_values,
                    deleteElems=options.delete_elements,
                    deleteAttributes=options.delete_attributes
                )
                out_stream = doRewrite(
                    rewriter, out_stream, rewriter.modify_elements)

        if options.doMaven:
            if options.mavenMultiProjectsDirs:
                for elem in options.mavenMultiProjectsDirs:
                    newcp += ":" + elem

            rewriter = DomRewriter()
            out_stream = doRewrite(
                rewriter,
                out_stream,
                rewriter.add_gentoo_classpath,
                classpath=newcp)

            deleteElems = []
            deleteAttributes = []
            deleteElems.append("target")
            deleteAttributes.append("depends")
            rewriter = SaxRewriter(
                deleteElems=deleteElems,
                deleteAttributes=deleteAttributes)
            out_stream = doRewrite(
                rewriter, out_stream, rewriter.modify_elements)

        return out_stream

    options_list = [
        make_option(
            "-a",
            "--attribute",
            action="append",
            dest="attributes",
            help="Attribute of the matching elements to change. These can be chained for multiple value-attribute pairs"),
        make_option(
            "-b",
            "--target-element",
            action="append",
            dest="target_elements",
            help="Tag of the element of which the attributes to be changed just in target scope.  These can be chained for multiple elements."),
        make_option(
            "-c",
            "--change",
            action="store_true",
            dest="doAdd",
            default=False,
            help="Change the value of an attribute.  If it does not exist, it will be created."),
        make_option(
            "-d",
            "--delete",
            action="store_true",
            dest="doDelete",
            default=False,
            help="Delete an attribute from matching elements."),
        make_option(
            "-e",
            "--element",
            action="append",
            dest="elements",
            help="Tag of the element of which the attributes to be changed.  These can be chained for multiple elements."),
        make_option(
            "-f",
            "--file",
            action="append",
            dest="files",
            help="Transform files instead of operating on stdout and stdin"),
        make_option(
            "-g",
            "--gentoo-classpath",
            action="store_true",
            dest="gentoo_classpath",
            help="Rewrite build.xml to use gentoo.classpath where applicable."),
        make_option(
            "-i",
            "--index",
            type="int",
            dest="index",
            help="Index of the match.  If none is specified, the changes will be applied to all matches within the document. Starts from zero."),
        make_option(
            "-j",
            "--javadoc",
            action="store_true",
            dest="doJavadoc",
            default=False,
            help="add a basic javadoc target. Sources must be placed in ${WORKDIR}/javadoc_src."),
        make_option(
            "-k",
            "--target-attribute",
            action="append",
            dest="target_attributes",
            help="Attribute of the matching elements to change. These can be chained for multiple value-attribute pairs (for targetonly)"),
        make_option(
            "-l",
            "--target-value",
            action="append",
            dest="target_values",
            help="Value to set the attribute to (targeronly)."),
        make_option(
            "-m",
            "--delete-attribute",
            action="append",
            dest="delete_attributes",
            help="Attribute of the matching elements to delete. These can be chained for multiple value-attribute pairs"),
        make_option(
            "-n",
            "--delete-element",
            action="append",
            dest="delete_elements",
            help="Tag of the element of which the attributes to be deleted.  These can be chained for multiple elements."),
        make_option(
            "-o",
            "--output-directory",
            action="append",
            dest="javadoc_dir",
            help="javadoc output directory. Must be an existing directory"),
        make_option(
            "-p",
            "--source-directory",
            action="append",
            dest="src_dirs",
            help="source directory for javadoc generation. Must be an existing directory"),
        make_option(
            "-q",
            "--maven-cleaning",
            action="store_true",
            dest="doMaven",
            default=False,
            help="Turns on maven generated build.xml cleanup rewriting."),
        make_option(
            "-r",
            "--source-element",
            action="append",
            dest="source_elements",
            help="Tag of the element of which the attributes to be changed just in source scope.  These can be chained for multiple elements."),
        make_option(
            "-s",
            "--multi-project-dirs",
            action="append",
            dest="mavenMultiProjectsDirs",
            help="Dirs in classpath notation"),
        make_option(
            "-t",
            "--source-attribute",
            action="append",
            dest="source_attributes",
            help="Attribute of the matching elements to change. These can be chained for multiple value-attribute pairs (for source only)"),
        make_option(
            "-v",
            "--value",
            action="append",
            dest="values",
            help="Value to set the attribute to."),
        make_option(
            "-y",
            "--source-value",
            action="append",
            dest="source_values",
            help="Value to set the attribute to. (sourceonly)")
    ]

    parser = OptionParser(usage, options_list)
    (options, args) = parser.parse_args()

    # Invalid Arguments Must be smited!
    if not options.doAdd and not options.doDelete and not options.gentoo_classpath and not options.doJavadoc and not options.doMaven:
        print(usage)
        print()
        error("No action was specified.")

    if options.doAdd:
        if not options.elements and not options.target_elements and not options.source_elements:
            error(
                "At least one element (global, source only or target only) and attribute must be specified.")

        for elem in (options.source_attributes or []):
            if elem in (options.attributes or []):
                error(
                    "You can't set an attribute in global and source scope at the same time")

        for elem in (options.target_attributes or []):
            if elem in (options.attributes or []):
                error(
                    "You can't set an attribute in global and target scope at the same time")

        if options.doAdd and (len(options.values or []) != len(options.attributes or [])
                              or len(options.source_values or []) != len(options.source_attributes or [])
                              or len(options.target_values or []) != len(options.target_attributes or [])):
            error(
                "You must give attribute(s)/value(s) for every element you are changing.")

    if options.doJavadoc:
        if len(options.src_dirs or []) < 1:
            error("You must specify as least one src directory.")

        for dir in options.src_dirs:
            if not os.path.isdir(dir):
                error("You must specify  existing directory for src output")

        if len(options.javadoc_dir or []) != 1:
            error("You must specify one and only one javadoc output directory.")

        if not os.path.isdir(options.javadoc_dir[0]):
            error("You must specify an existing directory for javadoc output")

    if options.doDelete:
        if not options.delete_elements:
            error("At least one element to delete must be specified.")

        if options.doDelete and (len(options.attributes or []) < 0):
            error(
                "You must give attribute(s) to delete for every element you are changing.")
            # End Invalid Arguments Check

    # main loop
    if options.files:
        for file in options.files:
            print("Rewriting %s" % file)
            # First parse the file into memory
            # Tricks with cwd are needed for relative includes of other xml
            # files to build.xml files
            cwd = os.getcwd()
            dirname = os.path.dirname(file)
            if dirname != '':  # for file = build.xml comes out as ''
                os.chdir(os.path.dirname(file))

            f = open(os.path.basename(file), "r")
            outxml = processActions(options, f)
            os.chdir(cwd)
            f.close()
            # Then write it back to the file
            f = open(file, "w")
            f.write(outxml)
            f.close()

    else:
        outxml = processActions(options, sys.stdin)
        sys.stdout.write(outxml)


if __name__ == '__main__':
    main()
