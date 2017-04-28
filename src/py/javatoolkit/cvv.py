# Copyright 2005, Thomas Matthijs <axxo@gentoo.org>
# Copyright 1999-2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

import os
import sys
from struct import unpack
from zipfile import ZipFile


class cvv:
    def __init__(self, target):
        self.target = target
        self.good = []
        self.bad = []

    def add(self, version, jar, file):
        if version <= self.target:
            self.good.append(("1."+str(version), jar, file))
        else:
            self.bad.append(("1."+str(version), jar, file))

    def do_class(self,filename):
        classFile = file(filename,"rb")
        classFile.seek(4)
        temp = classFile.read(4)
        (version,) = unpack('>xxh',temp)
        version -= 44
        self.add(version, None, filename)

    def do_jar(self, filename):
        zipfile = ZipFile(filename, 'r')

        for file in zipfile.namelist():
            if file.endswith('class'):
                classFile = zipfile.read(file)
                (version,) = unpack('>h',classFile[6:8])
                version -= 44
                self.add(version, filename, file)

    def do_file(self, filename):
        if not os.path.islink(filename):
            if filename.endswith(".class"):
                self.do_class(filename)
            if filename.endswith(".jar"):
                self.do_jar(filename)

# vim: set expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap:
