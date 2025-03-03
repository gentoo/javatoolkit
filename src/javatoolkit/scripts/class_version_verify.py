#!/usr/bin/env python3
# Copyright(c) 2005, Thomas Matthijs <axxo@gentoo.org>
# Copyright(c) 2005, Gentoo Foundation
# Distributed under the terms of the GNU General Public Licence v2

import os
import sys
from optparse import OptionParser, make_option
from .. import cvv


def main() -> None:
    options_list = [
        make_option(
            "-r",
            "--recurse",
            action="store_true",
            dest="deep",
            default=False,
            help="go into dirs"),
        make_option(
            "-t",
            "--target",
            type="string",
            dest="version",
            help="target version that is valid"),
        make_option(
            "-v",
            "--verbose",
            action="store_true",
            dest="verbose",
            default=False,
            help="Print details about analyzed files"),
        make_option(
            "-s",
            "--silent",
            action="store_true",
            dest="silent",
            default=False,
            help="No output"),
        make_option(
            "--detailed-output",
            action="store_true",
            dest="detailed_output",
            default=False,
            help="Include more details in messages"),
        make_option(
            "-f",
            "--file-only",
            action="store_true",
            dest="file_only",
            default=False,
            help="Only output the files"),
    ]

    parser = OptionParser(
        "%prog -t version [-r] [-v] [-s] <class/jar files or dir>",
        options_list)
    (options, args) = parser.parse_args()

    if not options.version:
        print("-t is mandatory")
        sys.exit(2)

    cvv_magic = cvv.CVVMagic(options.version)

    for arg in args:
        if os.path.isfile(arg):
            cvv_magic.do(arg)

        if options.deep and os.path.isdir(arg):
            for root, dirs, files in os.walk(arg):
                for filename in files:
                    cvv_magic.do("%s/%s" % (root, filename))

    if options.file_only:
        lst = set()
        for info in cvv_magic.bad:
            match info.loc:
                case cvv.FileLoc(path) | cvv.JarLoc(cvv.FileLoc(path), _):
                    lst.add(path)
        for i in lst:
            print(i)
    else:
        formatter: Formatter
        if options.detailed_output:
            formatter = FormatterV2()
        else:
            formatter = FormatterV1()

        if options.verbose:
            for good in cvv_magic.good:
                print(formatter.format_good(good))

        if not options.silent:
            for bad in cvv_magic.bad:
                print(formatter.format_bad(bad))
            for skipped in cvv_magic.skipped:
                print(formatter.format_skip(skipped))

        print(f'CVV: {options.version}')
        print(__get_total_line(cvv_magic))

    if len(cvv_magic.bad) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


class Formatter:
    def format_good(self, good_file: cvv.GoodFile) -> str:
        raise NotImplementedError()

    def format_bad(self, good_file: cvv.BadFile) -> str:
        raise NotImplementedError()

    def format_skip(self, good_file: cvv.SkippedFile) -> str:
        raise NotImplementedError()

class FormatterV1(Formatter):
    def format_good(self, f: cvv.GoodFile) -> str:
        return f'Good: {self.__format_class(f)}'

    def format_bad(self, f: cvv.BadFile) -> str:
        msg: str
        match f:
            case cvv.ClassFile():
                msg = f'{self.__format_class(f)}'
            case cvv.BadMultireleaseManifest(loc, multiReleaseDirs):
                plain_dirs = [d.member for d in multiReleaseDirs]
                msg = f'{self.__format_loc(loc)} missing "Multi-Release: true" for {plain_dirs}'
        return f'Bad: {msg}'

    def format_skip(self, f: cvv.SkippedFile) -> str:
        msg: str
        match f:
            case cvv.SkippedModuleInfo() as cf:
                msg = self.__format_class(cf)
            case cvv.SkippedVersionDir(loc, reason):
                msg = f'{self.__format_loc(loc)} because "{reason}"'
        return f'Skipped: {msg}'


    def __format_loc(self, loc: cvv.Loc) -> str:
        match loc:
            case cvv.FileLoc(path):
                return f'None {path}'
            case cvv.JarLoc(jar, member):
                return f'{jar.path} {member}'

    def __format_class(self, class_file: cvv.ClassFile) -> str:
        return f'{class_file.encoded_version} {self.__format_loc(class_file.loc)}'


class FormatterV2(Formatter):
    def format_good(self, f: cvv.GoodFile) -> str:
        return f'Good: {self.__format_class(f)}'

    def format_bad(self, f: cvv.BadFile) -> str:
        msg: str
        match f:
            case cvv.ClassFile():
                msg = f'{self.__format_class(f)}'
            case cvv.BadMultireleaseManifest(loc, multiReleaseDirs):
                plain_dirs = [d.member for d in multiReleaseDirs]
                msg = f'{self.__format_loc(loc)} missing "Multi-Release: true" implied by {plain_dirs}'
        return f'Bad:  {msg}'

    def format_skip(self, f: cvv.SkippedFile) -> str:
        return f'Skip: {self.__format_loc(f.loc)} because: {f.reason}'

    def __format_loc(self, loc: cvv.Loc) -> str:
        match loc:
            case cvv.FileLoc(path):
                return f'{path}'
            case cvv.JarLoc(jar, member):
                return f'{jar.path}({member})'

    def __format_class(self, cf: cvv.ClassFile) -> str:
        return f'{self.__format_loc(cf.loc)} version {cf.encoded_version} (expected {cf.expected_version})'


def __get_total_line(cvv_magic: cvv.CVVMagic) -> str:
    good = len(cvv_magic.good)
    bad = len(cvv_magic.bad)
    skipped = len(cvv_magic.skipped)
    total = good + bad + skipped
    return f'Checked: {total} Good: {good} Bad: {bad} Skipped: {skipped}'


if __name__ == '__main__':
    main()
