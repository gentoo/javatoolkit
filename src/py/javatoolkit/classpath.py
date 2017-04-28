# Copyright(c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright(c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2


class ClasspathIter:
    """An iterator for the Classpath class, below."""
    def __init__(self, classpath):
        self._classpath = classpath
        self._index = 0

    def __next__(self):
        self._index += 1
        if self._index >= len(self._classpath.classpath):
            raise StopIteration
        return self._classpath.classpath[self._index]


class Classpath:
    """A classpath object provides a collection interface to the elements of a : separated  path list. """
    def __init__(self, classpath_string = None):
        if classpath_string != None:
            cs = classpath_string.strip().strip("\"")
            self.classpath = cs.split(":")
        else:
            self.classpath = []

    def __iter__(self):
        """Returns iterator. Elements of the original classpath string are considered split by ':'."""
        return ClasspathIter(self)

    def __len__(self):
        """Returns length (number of elements) in this classpath."""
        return len(self.classpath)

    def __getitem__(self, i):
        """Returns i'th element."""
        return self.classpath[i]

    def __setitem__(self, i, val):
        """Sets i'th element."""
        self.classpath[i] = val

    def __str__(self):
        """Constructs a suitable string representation of the classpath."""
        return ":".join(self.classpath)

    def append(self, element):
        """Appends an path to the classpath."""
        self.classpath.append(element)


# vim: set expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap:
