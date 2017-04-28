#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# vim: set ai ts=8 sts=0 sw=8 tw=0 noexpandtab:

# Copyright 2004-2007 Gentoo Foundation
# Distributed under the terms of the GNU General Public Licence v2

# Authors:
# kiorky <kiorky@cryptelium.net>:
# Maintainer: Gentoo Java Herd <java@gentoo.org>
# Python based POM navigator

# ChangeLog
# kiorky <kiorky@cryptelium.net>:
# 31/05/2007 Add rewrite feature
#
# kiorky <kiorky@cryptelium.net>:
# 08/05/2007 initial version


import sys
import io
from optparse import OptionParser, make_option
from javatoolkit.maven.MavenPom import MavenPom


__version__ = "$Revision: 1.1 $"[11:-2]


def main()

    usage = "XML MAVEN POM MODULE " + __version__ + "\n"
    usage += "Copyright 2004,2006,2007 Gentoo Foundation\n"
    usage += "Distributed under the terms of the GNU General Public Lincense v2\n"
    usage += "Please contact the Gentoo Java Team <java@gentoo.org> with problems.\n"
    usage += "\n"
    usage += "Usage:\n"
    usage += "  %s [-a] [-v] [-g] [-d] [-f fic.xml]\n" % sys.argv[0]
    usage += "Or:\n"
    usage += "  %s --rewrite [--classpath some.jar:class.jar:path.jar] [--source JVM_VER ] |--target JVM_VER]\n" % sys.argv[0]
    usage += "    JVM_VER ::= 1.4 || 1.5 "
    usage += "\n"
    usage += "If the -f parameter is not utilized, the script will read and\n"
    usage += "write to stdin and stdout respectively.  The use of quotes on\n"
    usage += "parameters will break the script.\n"


    def error(message):
        print("ERROR: " + message)
        sys.exit(1)


    def doAction(stream,options):
        pom = MavenPom(options)
        if options.p_rewrite:
            pom.parse(stream, pom.rewrite)
        elif options.p_ischild or options.p_group or options.p_dep or options.p_artifact or options.p_version:
            pom.parse(stream, pom.getDescription)
        return pom


    def run():
        if options.files:
            import os
            for file in options.files:
                # First parse the file into memory
                cwd = os.getcwd()
                dirname = os.path.dirname(file)
                if dirname != '': # for file  comes out as ''
                    os.chdir(os.path.dirname(file))

                f = open(os.path.basename(file),"r")
                fs = f.read()
                f.close()
                # parse file and return approtiate pom object
                pom = doAction(fs,options)
                if options.p_rewrite:
                    f = open(os.path.basename(file),"w")
                    f.write(pom.read())
                    f.close()
                else:
                    print("%s" % pom.read())
                os.chdir(cwd)
        else:
            # process stdin
            pom = doAction(sys.stdin.read(),options)
            print(pom.read())


############### MAIN ###############
    options_list = [
        make_option ("-a", "--artifact", action="store_true", dest="p_artifact", help="get artifact name."),
        make_option ("-c", "--classpath", action="append", dest="classpath", help="set classpath to use with maven."),
        make_option ("-s", "--source", action="append", dest="p_source", help="Java source version."),
        make_option ("-t", "--target", action="append", dest="p_target", help="Java target version."),
        make_option ("-d", "--depependencies" , action="store_true", dest="p_dep",  help="get dependencies infos"),
        make_option ("-f", "--file",     action="append",     dest="files",      help="Transform files instead of operating on stdout and stdin"),
        make_option ("-g", "--group"   , action="store_true", dest="p_group",    help="get artifact group."),
        make_option ("-r", "--rewrite",  action="store_true", dest="p_rewrite", help="rewrite poms to use our classpath"),
        make_option ("-p", "--ischild",  action="store_true", dest="p_ischild", help="return true if this is a child pom"),
        make_option ("-v", "--version" , action="store_true", dest="p_version",  help="get artifact version."),
    ]

    parser = OptionParser(usage, options_list)
    (options, args) = parser.parse_args()

    # Invalid Arguments Must be smited!
    if not options.p_ischild and not options.p_rewrite and not options.p_dep and not options.p_version and not options.p_artifact and not options.p_group:
        print(usage)
        print()
        error("No action was specified.")

    if options.files:
        if len(options.files) > 1:
            error("Please specify only one pom at a time.")

    if options.p_rewrite:
        valid_sources = ["1.4","1.5"]
        for source in valid_sources:
            if options.p_source:
                if len(options.p_source) != 1:
                    error("Please specify one and only one source.")
                if options.p_source[0] not in valid_sources:
                    error("Source %s is not valid" % options.p_source[0])
            if options.p_target:
                if len(options.p_target) != 1:
                    error("Please specify one and only one target.")
                if options.p_target[0] not in valid_sources:
                    error("Target %s is not valid" % options.p_target[0])

        # join any classpathes if any
        if options.classpath:
            if len(options.classpath) > 1:
                start =[]
                start.append(options.classpath[0])
                for item in options.classpath[1:]:
                    start[0] += ":%s" % (item)
                options.classpath = start

    # End Invalid Arguments Check
    # main loop
    run()

if __name__ == '__main__':
    main()
