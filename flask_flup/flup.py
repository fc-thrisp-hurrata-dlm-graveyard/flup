# -*- coding: utf-8 -*-
"""
flup
================
This module provides upload support for Flask. The basic pattern is to set up
an `UploadSet` object and upload your files to it.
"""
import os.path
import posixpath
from flask import current_app, Blueprint, send_from_directory, abort, url_for
from itertools import chain
from werkzeug import secure_filename, FileStorage, LocalProxy

_flup = LocalProxy(lambda: current_app.extensions['flup'])

# Extension presets
#: If your Web server has PHP installed and set to auto-run, you might want to
#: add ``php`` to the DENY setting.
class AllExcept(object):
    def __init__(self, items):
        self.items = items

    def __contains__(self, item):
        return item not in self.items

class All(object):
    def __contains__(self, item):
        return True

TEXT = ('txt',)
DOCUMENTS = tuple('rtf odf ods gnumeric abw doc docx xls xlsx'.split())
IMAGES = tuple('jpg jpe jpeg png gif svg bmp'.split())
AUDIO = tuple('wav mp3 aac ogg oga flac'.split())
DATA = tuple('csv ini json plist xml yaml yml'.split())
SCRIPTS = tuple('js php pl py rb sh'.split())
ARCHIVES = tuple('gz bz2 zip tar tgz txz 7z'.split())
EXECUTABLES = tuple('so exe dll'.split())
ALL = All()
DEFAULTS = TEXT + DOCUMENTS + IMAGES + DATA


class UploadNotAllowed(Exception):
    pass


def tuple_from(*iters):
    return tuple(itertools.chain(*iters))


def extension(filename):
    return filename.rsplit('.', 1)[-1]


def lowercase_ext(filename):
    if '.' in filename:
        main, ext = filename.rsplit('.', 1)
        return main + '.' + ext.lower()
    else:
        return filename.lower()


def addslash(url):
    if url.endswith('/'):
        return url
    return url + '/'


class UploadConfiguration(object):
    def __init__(self, destination, base_url=None, allow=(), deny=()):
        self.destination = destination
        self.base_url = base_url
        self.allow = allow
        self.deny = deny

    @property
    def tuple(self):
        return (self.destination, self.base_url, self.allow, self.deny)

    def __eq__(self, other):
        return self.tuple == other.tuple


class UploadSet:
    def __init__(self, name='files', extensions=DEFAULTS):
        if not name.isalnum():
            raise ValueError("Name must be alphanumeric (no underscores)")
        self.name = name
        self.extensions = extensions
        self._config = None

    @property
    def config(self):
        if self._config is not None:
            return self._config
        try:
            return _flup.upload_sets_config[self.name]
        except AttributeError:
            raise RuntimeError("cannot access configuration outside request")

    def url(self, filename):
        base = self.config.base_url
        if base is None:
            return url_for('_uploads.uploaded_file', setname=self.name,
                           filename=filename, _external=True)
        else:
            return base + filename

    def path(self, filename, folder=None):
        if folder:
            target_folder = os.path.join(self.config.destination, folder)
        else:
            target_folder = self.config.destination
        return os.path.join(target_folder, filename)

    def file_allowed(self, storage, basename):
        return self.extension_allowed(extension(basename))

    def extension_allowed(self, ext):
        return ((ext in self.config.allow) or
                (ext in self.extensions and ext not in self.config.deny))

    def save(self, storage, folder=None, name=None):
        if not isinstance(storage, FileStorage):
            raise TypeError("storage must be a werkzeug.FileStorage")

        if folder is None and name is not None and "/" in name:
            folder, name = name.rsplit("/", 1)

        basename = lowercase_ext(secure_filename(storage.filename))
        if name:
            if name.endswith('.'):
                basename = name + extension(basename)
            else:
                basename = name

        if not self.file_allowed(storage, basename):
            raise UploadNotAllowed()

        if folder:
            target_folder = os.path.join(self.config.destination, folder)
        else:
            target_folder = self.config.destination
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        if os.path.exists(os.path.join(target_folder, basename)):
            basename = self.resolve_conflict(target_folder, basename)

        target = os.path.join(target_folder, basename)
        storage.save(target)
        if folder:
            return posixpath.join(folder, basename)
        else:
            return basename

    def resolve_conflict(self, target_folder, basename):
        name, ext = basename.rsplit('.', 1)
        count = 0
        while True:
            count = count + 1
            newname = '{}_{:d}.{}'.format(name, count, ext)
            if not os.path.exists(os.path.join(target_folder, newname)):
                return newname


class TestingFileStorage(FileStorage):
    def __init__(self, stream=None, filename=None, name=None,
                 content_type='application/octet-stream', content_length=-1,
                 headers=None):
        FileStorage.__init__(self, stream, filename, name=name,
            content_type=content_type, content_length=content_length,
            headers=None)
        self.saved = None

    def save(self, dst, buffer_size=16384):
        if isinstance(dst, str):
            self.saved = dst
        else:
            self.saved = dst.name


class Flup(object):
    def __init__(self, app=None,
                       upload_sets=None):
        self.app = app
        self.upload_sets = self.is_single_set(upload_sets)
        self.upload_sets_config = {}

        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def is_single_set(self, upload_sets):
        if isinstance(upload_sets, UploadSet):
            return (upload_sets,)
        elif isinstance(upload_sets, list):
            return upload_sets
        else:
            raise TypeError("{}: upload sets must be single instance or list of uploadsets".format(upload_sets))

    def init_app(self, app):
        for uset in self.upload_sets:
            uset_config = self.config_for_set(uset, app)
            self.upload_sets_config[uset.name] = uset_config

        should_serve = any(s.base_url is None for s in iter(self.upload_sets_config.values()))

        if '_uploads' not in app.blueprints and should_serve:
            app.register_blueprint(self._blueprint)

        app.extensions['flup'] = self


    def config_for_set(self, uset, app):
        app_config = app.config
        prefix = 'UPLOADED_{}_'.format(uset.name.upper())
        using_defaults = False

        app_default_dest = app_config.get('UPLOADS_DEFAULT_DEST', None)
        app_default_url = app_config.get('UPLOADS_DEFAULT_URL', None)

        allow_extns = tuple(app_config.get('{}{}'.format(prefix,'ALLOW'), ()))
        deny_extns = tuple(app_config.get('{}{}'.format(prefix, 'DENY'), ()))
        destination = app_config.get('{}{}'.format(prefix, 'DEST'))
        base_url = app_config.get('{}{}'.format(prefix, 'URL'))

        if destination is None:
            if app_default_dest:
                destination = os.path.join(app_default_dest, uset.name)
                using_defaults = True

        if destination is None:
            raise RuntimeError("""
                               no destination for set designated '{}' as {}\n
                               no application config var for '{}'\n
                               """.format(uset.name,
                                          '{}{}'.format(prefix, 'DEST'),
                                          'UPLOADS_DEFAULT_DEST')
                               )

        if base_url is None and using_defaults and app_default_url:
            base_url = addslash(app_default_url) + uset.name + '/'

        return UploadConfiguration(destination, base_url, allow_extns, deny_extns)


    @property
    def _blueprint(self):
        uploads_blueprint = Blueprint('_uploads', __name__, url_prefix='/_uploads')

        def uploaded_file(setname, filename):
            config = _flup.upload_sets_config.get(setname, None)
            if config is None:
                abort(404)
            return send_from_directory(config.destination, filename)

        uploads_blueprint.add_url_rule('/<setname>/<path:filename>', view_func=uploaded_file)

        return uploads_blueprint
