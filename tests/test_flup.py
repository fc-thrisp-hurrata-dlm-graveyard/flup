# -*- coding: utf-8 -*-
"""
tests/test_flup.py
=====================

NOTE: All the filenames in this testing file are in the POSIX style.
"""

from __future__ import with_statement
import os.path
import unittest
from flask import Flask, url_for
from flask.ext.flup import Flup
from flask.ext.flup.flup import (UploadSet, UploadConfiguration, extension,
    TestingFileStorage, addslash, ALL, AllExcept)

class TestTestingCase(unittest.TestCase):
    def setUp(self):
        self.tfs = TestingFileStorage(filename='foo.bar')

    def test_tfs(self):
        self.assertEqual(self.tfs.filename, 'foo.bar')
        self.assertIsNone(self.tfs.name)
        self.assertIsNone(self.tfs.saved)
        self.tfs.save('foo_bar.txt')
        self.assertEqual(self.tfs.saved, 'foo_bar.txt')

    def test_extension(self):
        self.assertEqual(extension('foo.txt'), 'txt')
        self.assertEqual(extension('foo'), 'foo')
        self.assertEqual(extension('archive.tar.gz'), 'gz')
        self.assertEqual(extension('audio.m4a'), 'm4a')

    def test_addslash(self):
        self.assertEqual(addslash('http://localhost:4000'), 'http://localhost:4000/')
        self.assertEqual(addslash('http://localhost/uploads'), 'http://localhost/uploads/')
        self.assertEqual(addslash('http://localhost:4000/'), 'http://localhost:4000/')
        self.assertEqual(addslash('http://localhost/uploads/'), 'http://localhost/uploads/')

    def test_custom_iterables(self):
        self.assertIn('txt', ALL)
        self.assertIn('exe', ALL)
        ax = AllExcept(['exe'])
        self.assertIn('txt', ax)
        self.assertNotIn('exe', ax)


class ConfigurationCase(unittest.TestCase):

    def setUp(self):
        self.f, self.p = UploadSet('files'), UploadSet('photos')
        self.flup = Flup(upload_sets=[self.f, self.p])

    def test_manual(self):
        app = Flask(__name__)
        options = dict(
            UPLOADED_FILES_DEST = '/var/files',
            UPLOADED_FILES_URL = 'http://localhost:6001/',
            UPLOADED_PHOTOS_DEST = '/mnt/photos',
            UPLOADED_PHOTOS_URL = 'http://localhost:6002/'
            )
        app.config.update(options)
        self.flup.init_app(app)
        self.assertEqual(app.extensions['flup'].upload_sets_config['files'],
                         UploadConfiguration('/var/files', 'http://localhost:6001/'))
        self.assertEqual(app.extensions['flup'].upload_sets_config['photos'],
                         UploadConfiguration('/mnt/photos', 'http://localhost:6002/'))

    def test_selfserve(self):
        app = Flask(__name__)
        options = dict(
            UPLOADED_FILES_DEST = '/var/files',
            UPLOADED_PHOTOS_DEST = '/mnt/photos'
            )
        app.config.update(options)
        self.flup.init_app(app)
        self.assertEqual(app.extensions['flup'].upload_sets_config['files'],
                         UploadConfiguration('/var/files', None))
        self.assertEqual(app.extensions['flup'].upload_sets_config['photos'],
                         UploadConfiguration('/mnt/photos', None))

    def test_defaults(self):
        app = Flask(__name__)
        options = dict(
            UPLOADS_DEFAULT_DEST = '/var/uploads',
            UPLOADS_DEFAULT_URL = 'http://localhost:6000/'
        )
        app.config.update(options)
        self.flup.init_app(app)
        self.assertEqual(app.extensions['flup'].upload_sets_config['files'],
                         UploadConfiguration('/var/uploads/files',
                         'http://localhost:6000/files/'))
        self.assertEqual(app.extensions['flup'].upload_sets_config['photos'],
                         UploadConfiguration('/var/uploads/photos', 'http://localhost:6000/photos/'))

    def test_default_selfserve(self):
        app = Flask(__name__)
        app.config['UPLOADS_DEFAULT_DEST'] = '/var/uploads'
        self.flup.init_app(app)
        self.assertEqual(app.extensions['flup'].upload_sets_config['files'],
                         UploadConfiguration('/var/uploads/files', None))
        self.assertEqual(app.extensions['flup'].upload_sets_config['photos'],
                         UploadConfiguration('/var/uploads/photos', None))

    def test_mixed_defaults(self):
        app = Flask(__name__)
        options = dict(
            UPLOADS_DEFAULT_DEST = '/var/uploads',
            UPLOADS_DEFAULT_URL = 'http://localhost:6001/',
            UPLOADED_PHOTOS_DEST = '/mnt/photos',
            UPLOADED_PHOTOS_URL = 'http://localhost:6002/'
        )
        app.config.update(options)
        self.flup.init_app(app)
        self.assertEqual(app.extensions['flup'].upload_sets_config['files'],
                         UploadConfiguration('/var/uploads/files', 'http://localhost:6001/files/'))
        self.assertEqual(app.extensions['flup'].upload_sets_config['photos'],
                         UploadConfiguration('/mnt/photos', 'http://localhost:6002/'))


class PreconditionsCase(unittest.TestCase):

    def test_filenames(self):
        uset = UploadSet('files')
        uset._config = UploadConfiguration('/uploads')
        namepairs = (
            ('foo.txt', True),
            ('boat.jpg', True),
            ('warez.exe', False)
        )
        for name, result in namepairs:
            tfs = TestingFileStorage(filename=name)
            self.assertEqual(uset.file_allowed(tfs, name), result)

    def test_default_extensions(self):
        uset = UploadSet('files')
        uset._config = UploadConfiguration('/uploads')
        extpairs = (('txt', True), ('jpg', True), ('exe', False))
        for ext, result in extpairs:
            self.assertEqual(uset.extension_allowed(ext), result)


class SavingCase(unittest.TestCase):
    def setUp(self):
        self.old_makedirs = os.makedirs
        os.makedirs = lambda v: None

    def teardown(self):
        os.makedirs = self.old_makedirs
        del self.old_makedirs

    def test_saved(self):
        uset = UploadSet('files')
        uset._config = UploadConfiguration('/uploads')
        tfs = TestingFileStorage(filename='foo.txt')
        res = uset.save(tfs)
        self.assertEqual(res, 'foo.txt')
        self.assertEqual(tfs.saved, '/uploads/foo.txt')

    def test_save_folders(self):
        uset = UploadSet('files')
        uset._config = UploadConfiguration('/uploads')
        tfs = TestingFileStorage(filename='foo.txt')
        res = uset.save(tfs, folder='someguy')
        self.assertEqual(res, 'someguy/foo.txt')
        self.assertEqual(tfs.saved, '/uploads/someguy/foo.txt')

    def test_save_named(self):
        uset = UploadSet('files')
        uset._config = UploadConfiguration('/uploads')
        tfs = TestingFileStorage(filename='foo.txt')
        res = uset.save(tfs, name='file_123.txt')
        self.assertEqual(res, 'file_123.txt')
        self.assertEqual(tfs.saved, '/uploads/file_123.txt')

    def test_save_namedext(self):
        uset = UploadSet('files')
        uset._config =UploadConfiguration('/uploads')
        tfs = TestingFileStorage(filename='boat.jpg')
        res = uset.save(tfs, name='photo_123.')
        self.assertEqual(res, 'photo_123.jpg')
        self.assertEqual(tfs.saved, '/uploads/photo_123.jpg')

    def test_folder_namedext(self):
        uset = UploadSet('files')
        uset._config =UploadConfiguration('/uploads')
        tfs = TestingFileStorage(filename='boat.jpg')
        res = uset.save(tfs, folder='someguy', name='photo_123.')
        self.assertEqual(res, 'someguy/photo_123.jpg')
        self.assertEqual(tfs.saved, '/uploads/someguy/photo_123.jpg')

    def test_implicit_folder(self):
        uset = UploadSet('files')
        uset._config =UploadConfiguration('/uploads')
        tfs = TestingFileStorage(filename='boat.jpg')
        res = uset.save(tfs, name='someguy/photo_123.')
        self.assertEqual(res, 'someguy/photo_123.jpg')
        self.assertEqual(tfs.saved, '/uploads/someguy/photo_123.jpg')

    def test_secured_filename(self):
        uset = UploadSet('files', ALL)
        uset._config =UploadConfiguration('/uploads')
        tfs1 = TestingFileStorage(filename='/etc/passwd')
        tfs2 = TestingFileStorage(filename='../../myapp.wsgi')
        res1 = uset.save(tfs1)
        self.assertEqual(res1, 'etc_passwd')
        self.assertEqual(tfs1.saved, '/uploads/etc_passwd')
        res2 = uset.save(tfs2)
        self.assertEqual(res2, 'myapp.wsgi')
        self.assertEqual(tfs2.saved, '/uploads/myapp.wsgi')


class ConflictResolutionCase(unittest.TestCase):
    def setUp(self):
        self.extant_files = []
        self.old_exists = os.path.exists
        os.path.exists = self.exists
        self.old_makedirs = os.makedirs
        os.makedirs = lambda v: None

    def tearDown(self):
        os.path.exists = self.old_exists
        del self.extant_files, self.old_exists
        os.makedirs = self.old_makedirs
        del self.old_makedirs

    def extant(self, *files):
        self.extant_files.extend(files)

    def exists(self, fname):
        return fname in self.extant_files

    def test_self(self):
        self.assertFalse(os.path.exists('/uploads/foo.txt'))
        self.extant('/uploads/foo.txt')
        self.assertTrue(os.path.exists('/uploads/foo.txt'))

    def test_conflict(self):
        uset = UploadSet('files')
        uset._config =UploadConfiguration('/uploads')
        tfs = TestingFileStorage(filename='foo.txt')
        self.extant('/uploads/foo.txt')
        res = uset.save(tfs)
        self.assertEqual(res, 'foo_1.txt')

    def test_multi_conflict(self):
        uset = UploadSet('files')
        uset._config =UploadConfiguration('/uploads')
        tfs = TestingFileStorage(filename='foo.txt')
        self.extant('/uploads/foo.txt',
                    *('/uploads/foo_%d.txt' % n for n in range(1, 6)))
        res = uset.save(tfs)
        self.assertEqual(res, 'foo_6.txt')


class PathsUrlsCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            UPLOADED_FILES_DEST='/uploads'
        )

    def test_path(self):
        uset = UploadSet('files')
        uset._config = UploadConfiguration('/uploads')
        self.assertEqual(uset.path('foo.txt'), '/uploads/foo.txt')
        self.assertEqual(uset.path('someguy/foo.txt'), '/uploads/someguy/foo.txt')

    def test_url_generated(self):
        uset = UploadSet('files')
        Flup(self.app, uset)
        with self.app.test_request_context():
            url = uset.url('foo.txt')
            gen = url_for('_uploads.uploaded_file', setname='files',
                      filename='foo.txt', _external=True)
            self.assertEqual(url, gen)

    def test_url_based(self):
        app = Flask(__name__)
        app.config.update(
            UPLOADED_FILES_DEST='/uploads',
            UPLOADED_FILES_URL='http://localhost:5001/'
        )
        uset = UploadSet('files')
        Flup(app, uset)
        with app.test_request_context():
            url = uset.url('foo.txt')
            self.assertEqual(url, 'http://localhost:5001/foo.txt')
        self.assertNotIn('_uploads', app.modules)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTestingCase))
    suite.addTest(unittest.makeSuite(ConfigurationCase))
    suite.addTest(unittest.makeSuite(PreconditionsCase))
    suite.addTest(unittest.makeSuite(SavingCase))
    suite.addTest(unittest.makeSuite(ConflictResolutionCase))
    suite.addTest(unittest.makeSuite(PathsUrlsCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
