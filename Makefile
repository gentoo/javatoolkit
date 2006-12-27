# Copyright 2003-2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2003-2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header: /var/cvsroot/gentoo-src/javatoolkit/Makefile,v 1.3 2004/12/25 00:14:05 axxo Exp $

include makedefs.mak


all:
	echo $(PYVERSION)
	echo $(VERSION)
	echo $(docdir)
	echo $(bindir)
	echo $(sbindir)
	echo $(mandir)
	for x in bsfix; do \
		( cd src/$$x; $(MAKE) all ) \
	done

dist: dist-javatoolkit

dist-javatoolkit:
	mkdir -p release/javatoolkit-$(VERSION)$(RELEASE_TAG)
	rm -rf release/javatoolkit-$(VERSION)$(RELEASE_TAG)/
	for x in sun-fetch findclass bsfix buildparser javatoolkit ; do \
		( cd src/$$x ; $(MAKE) distdir=release/javatoolkit-$(VERSION)$(RELEASE_TAG) dist ) \
	done
	cp Makefile AUTHORS README TODO COPYING NEWS ChangeLog release/javatoolkit-$(VERSION)$(RELEASE_TAG)/
	cat makedefs.mak | \
		sed "s/^VERSION=.*/VERSION=$(VERSION)/" | \
		sed "s/^RELEASE_TAG=.*/RELEASE_TAG=$(RELEASE_TAG)/" \
		> release/javatoolkit-$(VERSION)$(RELEASE_TAG)/makedefs.mak
	( cd release ; tar jcf javatoolkit-$(VERSION)$(RELEASE_TAG).tar.bz2 javatoolkit-$(VERSION)$(RELEASE_TAG)/ )

install: install-javatoolkit

install-javatoolkit:

	install -d $(docdir)
	install -d $(bindir)
	install -d $(sbindir)
	install -d $(mandir)

	install -m 0644 AUTHORS ChangeLog COPYING NEWS README TODO $(docdir)/

	for x in sun-fetch findclass bsfix buildparser javatoolkit ; do \
		( cd src/$$x ; $(MAKE) DESTDIR=$(DESTDIR) install )  \
	done

upload:
	scp release/javatoolkit-$(VERSION)$(RELEASE_TAG).tar.bz2 $(USER)@dev.gentoo.org:/space/distfiles-local/
