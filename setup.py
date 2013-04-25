"""
Flask-Uploads
-------------
Flask-Uploads provides flexible upload handling for Flask applications. It
lets you divide your uploads into sets that the application user can publish
separately.

Links
`````
* `documentation <http://packages.python.org/Flask-Uploads>`_
* `development version
  <http://bitbucket.org/leafstorm/flask-uploads/get/tip.gz#egg=Flask-Uploads-dev>`_


"""
from setuptools import setup
from flask_flup import __version__

setup(
    name='Flup',
    version=__version__,
    url='',
    license='MIT',
    author='Thrisp/Hurrata',
    author_email='blueblank@gmail.com',
    description='Flexible and efficient upload handling for Flask',
    long_description=__doc__,
    packages=['flask_flup'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.9'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
