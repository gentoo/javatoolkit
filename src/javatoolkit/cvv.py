# Copyright 2005, Thomas Matthijs <axxo@gentoo.org>
# Copyright 1999-2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from dataclasses import dataclass
from struct import unpack
from zipfile import ZipFile
import os
import re
import typing as T


@dataclass(frozen=True)
class FileLoc:
    path: str


@dataclass(frozen=True)
class JarLoc:
    '''A file inside a jar archive'''
    jar: FileLoc
    member: str


Loc = FileLoc | JarLoc


@dataclass
class ClassFile:
    loc: Loc
    encoded_version: str
    expected_version: str


@dataclass
class BadMultireleaseManifest:
    '''A multi-release jar but without `Multi-Release: true` in MANIFEST.MF'''
    loc: JarLoc
    multiReleaseDirs: list[JarLoc]


@dataclass
class SkippedVersionDir:
    loc: JarLoc
    reason: str


@dataclass
class SkippedModuleInfo:
    loc: Loc
    reason: str = 'A module-info requires java release >= 9'


GoodFile = ClassFile
BadFile = ClassFile | BadMultireleaseManifest
SkippedFile = SkippedVersionDir | SkippedModuleInfo


class CVVMagic:
    def __init__(self, target: str) -> None:
        # this is a number 8 9 10 11 etc, not including 1.
        if '.' in target:
            self.target = int(target.split(".")[-1])
        else:
            self.target = int(target)
        self.good: list[GoodFile] = []
        self.bad: list[BadFile] = []
        self.skipped: list[SkippedFile] = []

    def add(self, version: int, loc: Loc, target_version: T.Optional[int] = None) -> None:
        if target_version is None:
            target_version = self.target

        if CVVMagic.__is_module_info(loc) and target_version < 9:
            self.__on_skipped(SkippedModuleInfo(loc))
            return

        cf = ClassFile(
            loc,
            encoded_version=self.__format_version(version),
            expected_version=self.__format_version(target_version))

        if version <= target_version:
            self.__on_good(cf)
        else:
            self.__on_bad(cf)

    def do_class(self, class_file: T.IO[bytes], filename: FileLoc) -> None:
        version = self.__extract_version(class_file)
        self.add(version, filename)

    def do_jar(self, jar: ZipFile, jar_path: FileLoc) -> None:
        def jar_loc(path: str) -> JarLoc:
            return JarLoc(jar_path, path)

        is_multirelease = False
        try:
            manifest = jar.open('META-INF/MANIFEST.MF', 'r')
        except KeyError:
            pass
        else:
            with manifest:
                def decode_line(line: bytes) -> str:
                    # The Manifest spec requires that the file is utf-8 encoded.
                    # Unfortunately, stuff like the maven-jar-plugin can generate
                    # an invalid manifest when it blindly copies the author name
                    return line.decode('utf-8', 'replace').rstrip('\r\n')
                lines = [decode_line(line) for line in manifest.readlines()]
                is_multirelease = 'Multi-Release: true' in lines

        invalid_version_dirs: set[str] = set()
        seen_skipped_dirs: set[str] = set()
        for path in jar.namelist():
            if not path.endswith('class'):
                continue

            loc = jar_loc(path)

            with jar.open(path, 'r') as class_file:
                target_version = None
                match self.__get_multirelease_target_version(path):
                    case int(tv):
                        if is_multirelease:
                            target_version = tv
                        else:
                            version_dir = path.split('/', 3)[:3]
                            invalid_version_dirs.add('/'.join(version_dir))
                            continue
                    case (ver_dir, reason):
                        if ver_dir not in seen_skipped_dirs:
                            seen_skipped_dirs.add(ver_dir)
                            self.__on_skipped(SkippedVersionDir(
                                jar_loc(ver_dir), reason))
                        continue
                    case None:
                        pass

                version = self.__extract_version(class_file)
                self.add(version, loc, target_version)

        if len(invalid_version_dirs):
            self.__on_bad(BadMultireleaseManifest(
                jar_loc('META-INF/MANIFEST.MF'),
                [jar_loc(d) for d in sorted(invalid_version_dirs)]))

    def do(self, filename: str) -> None:
        if not os.path.islink(filename):
            if filename.endswith(".class"):
                with open(filename, 'rb') as class_file:
                    self.do_class(class_file, FileLoc(filename))
            if filename.endswith(".jar"):
                with ZipFile(filename, 'r') as jar:
                    self.do_jar(jar, FileLoc(filename))

    @classmethod
    def __extract_version(cls, file: T.IO[bytes]) -> int:
        data = file.read(8)
        if len(data) != 8:
            raise ValueError(f'Need the first 8 bytes of a java .class file, got: {len(data)}')
        # A .class file is encoded like (all big-endian):
        # u4 - magic
        # u2 - minor version
        # u2 - major version
        result = unpack('>4x2xH', data)[0]
        return result - 44

    @classmethod
    def __get_multirelease_target_version(cls, path: str) -> int | None | tuple[str, str]:
        '''Get the target verion of a possible multi-release class file

        Returns:
        int target_version - If the path is under META-INF/versions/${target_version}
        None - If the path is not part of META-INF/versions
        (directory, reason) - The directory portion of `path` that should be ignored
        '''
        result = None

        parts = path.split('/', 3)
        if len(parts) >= 3 and parts[:2] == ['META-INF', 'versions']:
            expected_version = parts[2]
            # https://docs.oracle.com/en/java/javase/23/docs/specs/jar/jar.html#multi-release-jar-files
            # If the version is not a number or < 9 it is ignored

            ver_dir = '/'.join(parts[:3])
            reasonBase = f'The version directory "{expected_version}" '
            if not expected_version.isdecimal():
                return (ver_dir, reasonBase + 'is not a number')
            if (result := int(expected_version)) < 9:
                return (ver_dir, reasonBase + 'is less than 9')

        return result

    __module_info_jar_pattern = re.compile('(META-INF/versions/[1-9][0-9]*/)?module-info.class')
    __module_info_file_pattern = re.compile('module-info.class')

    @classmethod
    def __is_module_info(cls, filepath: Loc) -> bool:
        match filepath:
            case FileLoc(target):
                ptn = cls.__module_info_file_pattern
            case JarLoc(member=target):
                ptn = cls.__module_info_jar_pattern

        return ptn.fullmatch(target) is not None

    @classmethod
    def __format_version(cls, version: int) -> str:
        return f'1.{version}' if version < 9 else f'{version}'

    def __on_good(self, goodFile: GoodFile) -> None:
        self.good.append(goodFile)

    def __on_bad(self, badFile: BadFile) -> None:
        self.bad.append(badFile)

    def __on_skipped(self, skippedFile: SkippedFile) -> None:
        self.skipped.append(skippedFile)

# vim: set expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap:
