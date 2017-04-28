#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright 2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public Licence v2

# Authors
#   Alistair Bush <ali_bush@gentoo.org>

from __future__ import with_statement
import os
import sys
from optparse import OptionParser, make_option
from xml.dom.minidom import parse
from javatoolkit.java.properties import PropertiesParser


__version__ = "$Revision: 1 $"[11:-2]


if __name__ == '__main__':
    usage = "Eclipse Ant Build File writer " + __version__ + "\n"
    usage += "Copyright 2008 Gentoo Foundation\n"
    usage += "Distributed under the terms of the GNU General Public Licence\n"
    usage += "Please contact the Gentoo Java Team <java@gentoo.org> with problems.\n"
    usage += "\nJust wait till I finish this."

    option_list = [
        make_option ( '-p', '--project', action='store', dest='project', help='Project Name' ),
        make_option ( '-i', '--include', action='append', dest='includes', help='Files to include in jar' ),
        make_option ( '-s', '--src', action='append', dest='source', help='Directories containing src to build' ),
        make_option ( '-m', '--manifest', action='store', dest='manifest', help='Manifest File' ),
        make_option ( '-f', '--file', action='store', dest='file', help='Eclipse build.properties file to parse.' ),
        make_option ( '-o', '--output', action='store', dest='output', help='Output build.xml to this file' )
    ]

    parser = OptionParser( usage, option_list )
    (options, args) = parser.parse_args()
    #check parser options here.

    if options.file:
        properties = PropertiesParser( options.file )
        #dom = parse( options.file )
        #classpathentries = dom.getElementsByTagName('classpathentry')

        #for entry in classpathentries:
        #    if entry.attributes['kind'] and entry.attributes['kind'].nodeValue == 'src':
        #        print entry.attributes['path'].nodeValue
        #        if entry.attributes['path']:
        #            src_dirs.append( entry.attributes['path'].nodeValue )

        with open( options.output, 'w' ) as output:
            output.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
            output.write('<project basedir="." default="jar" name="'+options.project+'">\n')
            output.write('<property name="target" value="1.4"/>\n')
            output.write('<property name="source" value="1.4"/>\n')
            output.write('<property name="gentoo.classpath" value="" />\n\n')
            output.write('<target name="init">\n')
            output.write('<mkdir dir="bin"/>\n')
            output.write('<copy includeemptydirs="false" todir="bin">\n')
            try:
                if properties.config['source..']:
                    for dir in properties.config['source..']:
                        output.write('<fileset dir="'+dir+'" excludes="**/*.java, **/*.launch" />\n')
                if properties.config['bin.includes']:
                    for item in properties.config['bin.includes']:
                        if item != '.':
                            if item.endswith('/'):
                                item = item.rstrip('/')
                                output.write('<fileset dir="." includes="'+item+'/**" excludes="**/*.java, **/*.launch" />\n')
                            else:
                                output.write('<fileset file="'+item+'" />\n')
            finally:
                output.write('</copy>\n')
            if options.includes:
                for file in options.includes:
                    output.write('<copy file="'+file+'" todir="bin"/>')
            output.write('</target>\n')
            output.write('\n<target name="clean">\n\t<delete dir="bin"/>\n</target>\n\n')
            output.write('<target depends="init" name="compile">\n')
            output.write('<javac destdir="bin" source="${source}" target="${target}" classpath="${gentoo.classpath}">\n')
            try:
                if properties.config['source..']:
                    for dir in properties.config['source..']:
                        output.write('\t<src path="'+dir+'" />\n')
            finally:
                output.write('</javac>\n')
            output.write('</target>\n\n')
            output.write('<target depends="compile" name="jar" >\n')
            output.write('<jar file="${ant.project.name}.jar" basedir="bin"')
            if options.manifest:
                output.write('\nmanifest="'+parser.manifest+'">\n')
            else:
                output.write('>\n')
            output.write('</jar>\n')
            output.write('</target>\n')
            output.write('</project>\n')
            #output.write('')
            #output.write('')
            #output.write('')
            #output.write('')
            #output.write('')
            #output.write('')
            #output.write('')

# vim:set expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap :
