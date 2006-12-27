# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#
# $Header: /var/cvsroot/gentoo-src/javatoolkit/makedefs.mak,v 1.2 2004/08/10 20:38:58 karltk Exp $

# Override this on command line when making a release, ie 'dist'

VERSION=0.2.0
RELEASE_TAG=
PYVERSION="`python-config | sed 's/-l//' | sed 's/ -lm.*//'`"
DESTDIR=

docdir=$(DESTDIR)/usr/share/doc/javatoolkit-$(VERSION)$(RELEASE_TAG)
libdir=$(DESTDIR)/usr/lib/javatoolkit
bindir=$(DESTDIR)/usr/bin
sbindir=$(DESTDIR)/usr/sbin
mandir=$(DESTDIR)/usr/share/man/man1
