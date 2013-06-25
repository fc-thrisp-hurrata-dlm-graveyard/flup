"""
Flup
-------------
Flexible upload handling for Flask applications.
"""
from setuptools import setup
from flask_flup import __version__

setup(
    name='Flask-Flup',
    version=__version__,
    url='https://github.com/thrisp/flup.git',
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
    test_suite='tests',
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
