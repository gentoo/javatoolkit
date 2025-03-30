# Copyright(c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright(c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2

# FIXME: Use gentoolkit stuff instead
import sys


def eerror(s):
    sys.stderr.write("!!! " + s + "\n")


def ewarn(s):
    sys.stdout.write("* " + s + "\n")


def einfo(s):
    sys.stdout.write("* " + s + "\n")


def die(err, s):
    eerror(s)
    sys.exit(err)
