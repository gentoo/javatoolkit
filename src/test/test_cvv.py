from unittest import TestCase
import io
import javatoolkit.cvv as cvv
from zipfile import ZipFile
import struct
import typing as T


def create_class_header(version: int) -> bytes:
    magic = b'\xca\xfe\xba\xbe'
    minor = 0
    major = version + 44
    return magic + struct.pack('>2H', minor, major)


def create_class_file(version: int) -> io.BytesIO:
    return io.BytesIO(create_class_header(version))


def create_jar(files: list[tuple[str, int]], multi_release: bool = False) -> ZipFile:
    result = ZipFile(io.BytesIO(), 'w')
    for (path, version) in files:
        result.writestr(path, create_class_header(version))
    manifest = f'''Manifest-Version: 1.0
Created-By: 21.0.6 (javatoolkit mock)
Multi-Release: {'true' if multi_release else 'false'}
'''
    result.writestr('META-INF/MANIFEST.MF', manifest)
    return result


AnyFileInfo = T.TypeVar('AnyFileInfo',
                        bound=cvv.BadFile | cvv.GoodFile | cvv.SkippedFile)


def my_sort(lst: list[AnyFileInfo]) -> list[AnyFileInfo]:
    if len(lst) == 0:
        return lst

    def key_extractor(v: AnyFileInfo) -> tuple[str, str]:
        match v.loc:
            case cvv.JarLoc(cvv.FileLoc(path), member):
                return (path, member)
            case cvv.FileLoc(path):
                return (path, '')

    return sorted(lst, key=key_extractor)


class SimpleTest(TestCase):
    def test_class(self) -> None:
        m = cvv.CVVMagic('8')
        m.do_class(create_class_file(7), cvv.FileLoc('7.class'))
        m.do_class(create_class_file(8), cvv.FileLoc('8.class'))
        m.do_class(create_class_file(9), cvv.FileLoc('9.class'))

        def make_class(path: str, encoded_version: str) -> cvv.ClassFile:
            return cvv.ClassFile(
                encoded_version=encoded_version,
                expected_version='1.8',
                loc=cvv.FileLoc(path)
            )

        self.assertListEqual(my_sort(m.good), [
            make_class('7.class', '1.7'),
            make_class('8.class', '1.8'),
        ])
        self.assertListEqual(my_sort(m.bad), [
            make_class('9.class', '9')
        ])
        self.assertListEqual(m.skipped, [])

    def test_jar(self) -> None:
        m = cvv.CVVMagic('1.8')
        m.do_jar(jar_path=cvv.FileLoc('a.jar'), jar=create_jar([
            ('Main.class', 8),
            ('module-info.class', 9),
            ('my/deep/module/Foo.class', 10),
        ]))

        def jar_loc(path: str) -> cvv.JarLoc:
            return cvv.JarLoc(cvv.FileLoc('a.jar'), path)

        def make_class(path: str, encoded_version: str) -> cvv.ClassFile:
            return cvv.ClassFile(
                encoded_version=encoded_version,
                expected_version='1.8',
                loc=jar_loc(path)
            )

        def make_skip(path: str, ver: str) -> cvv.SkippedModuleInfo:
            return cvv.SkippedModuleInfo(jar_loc(path), ver, '1.8')

        self.assertListEqual(my_sort(m.good), [
            make_class('Main.class', '1.8'),
        ])
        self.assertListEqual(my_sort(m.bad), [
            make_class('my/deep/module/Foo.class', '10'),
        ])
        self.assertListEqual(my_sort(m.skipped), [
            make_skip('module-info.class', '9'),
        ])

    def test_multirelease_jar(self) -> None:
        m = cvv.CVVMagic('9')
        m.do_jar(jar_path=cvv.FileLoc('a.jar'), jar=create_jar(multi_release=True, files=[
            ('module-info.class', 9),
            ('File1.class', 9),
            ('File2.class', 8),
            ('META-INF/versions/10/module-info.class', 10),
            ('META-INF/versions/10/File1.class', 11),
            ('META-INF/versions/10/File2.class', 10),
            ('META-INF/versions/14/module-info.class', 15),
            ('META-INF/versions/14/File1.class', 13),
        ]))

        def make_class(path: str, encoded_version: str, expected_version: T.Optional[str] = None) -> cvv.ClassFile:
            return cvv.ClassFile(
                encoded_version=encoded_version,
                expected_version=expected_version or '9',
                loc=cvv.JarLoc(cvv.FileLoc('a.jar'), path),
            )

        self.assertListEqual(my_sort(m.good), [
            make_class('File1.class', '9'),
            make_class('File2.class', '1.8'),
            make_class('META-INF/versions/10/File2.class', '10', '10'),
            make_class('META-INF/versions/10/module-info.class', '10', '10'),
            make_class('META-INF/versions/14/File1.class', '13', '14'),
            make_class('module-info.class', '9'),
        ])
        self.assertListEqual(my_sort(m.bad), [
            make_class('META-INF/versions/10/File1.class', '11', '10'),
            make_class('META-INF/versions/14/module-info.class', '15', '14'),
        ])
        self.assertListEqual(m.skipped, [])

    def test_multirelease_invalid_ver(self) -> None:
        m = cvv.CVVMagic('10')
        m.do_jar(jar_path=cvv.FileLoc('b.jar'), jar=create_jar(multi_release=True, files=[
            ('Class.class', 10),
            ('META-INF/versions/8/Class.class', 8),
            ('META-INF/versions/hamburger/Class.class', 9874),
        ]))

        def jar_member(path: str) -> cvv.JarLoc:
            return cvv.JarLoc(cvv.FileLoc('b.jar'), path)

        def make_class(path: str, ver: str, expected: str) -> cvv.ClassFile:
            return cvv.ClassFile(jar_member(path), encoded_version=ver, expected_version=expected)

        self.assertListEqual(my_sort(m.good), [
            make_class('Class.class', '10', '10'),
        ])
        self.assertListEqual(my_sort(m.bad), [])
        self.assertListEqual(my_sort(m.skipped), [
            cvv.SkippedVersionDir(
                jar_member('META-INF/versions/8'),
                'The version directory "8" is less than 9'),
            cvv.SkippedVersionDir(
                jar_member('META-INF/versions/hamburger'),
                'The version directory "hamburger" is not a number'),
        ])

    def test_multirelease_no_manifest(self) -> None:
        m = cvv.CVVMagic('8')
        jar = cvv.FileLoc('a.jar')
        m.do_jar(create_jar(multi_release=False, files=[
            ('module/App.class', 8),
            ('module/Class.class', 8),
            ('META-INF/versions/9/module/App.class', 9),
            ('META-INF/versions/9/module/Class.class', 9),
            ('META-INF/versions/10/module/App.class', 10),
            ('META-INF/versions/10/module/Class.class', 10),
            # These 2 should be skipped, not reported as errors
            ('META-INF/versions/7/module/App.class', 7),
            ('META-INF/versions/7/module/Class.class', 8),
        ]), jar)

        def jar_member(path: str) -> cvv.JarLoc:
            return cvv.JarLoc(jar, path)

        def make_class(path: str) -> cvv.ClassFile:
            return cvv.ClassFile(
                encoded_version='1.8',
                expected_version='1.8',
                loc=jar_member(path))

        self.assertListEqual(my_sort(m.good), [
            make_class('module/App.class'),
            make_class('module/Class.class'),
        ])
        self.assertListEqual(my_sort(m.bad), [
            cvv.BadMultireleaseManifest(jar_member('META-INF/MANIFEST.MF'), [
                jar_member('META-INF/versions/10'),
                jar_member('META-INF/versions/9'),
            ]),
        ])
        self.assertListEqual(my_sort(m.skipped), [
            cvv.SkippedVersionDir(jar_member('META-INF/versions/7'),
                                  'The version directory "7" is less than 9'),
        ])

    def test_no_manifest(self):
        m = cvv.CVVMagic('10')
        jar_path = cvv.FileLoc('/path/to/a.jar')

        jar = ZipFile(io.BytesIO(), 'w')
        jar.writestr('module-info.class', create_class_header(10))

        m.do_jar(jar, jar_path)
        self.assertListEqual(m.good, [
            cvv.ClassFile(cvv.JarLoc(jar_path, 'module-info.class'), '10', '10'),
        ])
        self.assertListEqual(m.bad, [])
        self.assertListEqual(m.skipped, [])
