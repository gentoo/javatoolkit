# Copyright 2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
import os


class PropertiesParser:
    """
    Parse eclipse projects build.properties file.
    """

    def __init__( self, file ):
        self.file = file
        self.config = {}
        self.parse( file )

    def parse( self, file ):
        if not os.path.isfile(file):
            return
        if not os.access(file, os.R_OK):
            return

        stream = open( file, 'r' )
        line = stream.readline()
        while line != '':
            line = line.strip('\n')
            line = line.strip()
            if line.isspace() or line == '' or line.startswith('#'):
                line = stream.readline()
                continue

            index = line.find('=')
            name = line[:index]
            name = name.strip()
            value = line[index+1:]

            while line.endswith('\\'):
                line = stream.readline()
                line = line.strip('\n')
                line = line.strip()
                if line.isspace() or line == '' or line.startswith('#'):
                    line = stream.readline()
                    break
                value +=line

            value = value.strip('\\')

            if value == '':
                line = stream.readline()
                continue
            value = value.strip('\\\'\"').strip('\\').strip()
            value = value.replace('\\', '')
            self.config[name] = value.split(',')
            line = stream.readline()


# vim:set expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap :
