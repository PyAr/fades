#!/usr/bin/env python3

# Copyright 2014-2017 Facundo Batista, Nicolás Demarchi
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# For further info, check  https://github.com/PyAr/fades

"""Build tar.gz for fades.

Needed packages to run (using Debian/Ubuntu package names):

    python3
    python3-xdg   (optional)
    python3-pkg-resources
    python3-setuptools
"""

import os
import re
import shutil
import sys
import zlib

from distutils.core import setup
from setuptools.command.install import install

_PY2_MESSAGE = (
    b"x\x9c\xb5QA\x0e\x800\x08\xbb\xf3\nnjb\xb2\x0f-\xc1\x87\xec\xf1\x0e\xda\xe1f\xbc\xca2\x02\xa5"
    b"Ep\xa2j\xddt2\x9b\xfc\x97\xbd\xf9\x9f\x9cW\x9c\xb9h\xf3\xac>x\xd3Fo\xa3=T\xcc\x9b\x03U\x13"
    b"\xcb:\xafe\x0f\xa8{\xac\xbb\x1d,I\xd4\x0e\xf7y\xc0\xd9\xd0\xb5`\x9a\xccC\xe7|b\xd7\xa8"
    b"\xe3\x14\xaa\xddC}\xb1\x82N\xd8\xcf\nf\xa2\xcat\xfa\xfa\xbeL\x83\x1e\xce\xd7e\xc6"
    b"\xa1\xae\xb1\xfc\xd8\xcf\xd5\x93\xb6\xeb$xa\x9dz:ZcB^\xcfb\x9a\x91\xc7\xff4F+"
    b"\xef\x8c8\xe8\x95\xfb%\xcaNM\x9ew%\xf5G\x93\x1bF\xf1\x97\x0f")

# forbid the installation in a python2 environment
if sys.version_info.major < 3:
    print(zlib.decompress(_PY2_MESSAGE).decode('ascii'))
    print("fades is a python3 only project, sorry!\n")
    raise ValueError("fades is a python3 only project, sorry!")


def get_version():
    """Retrieves package version from the file."""
    with open('fades/_version.py') as fh:
        m = re.search("\(([^']*)\)", fh.read())
    if m is None:
        raise ValueError("Unrecognized version in 'fades/_version.py'")
    return m.groups()[0].replace(', ', '.')


# the different scripts according to the platform
SCRIPT_WIN = 'bin/fades.cmd'
SCRIPT_REST = 'bin/fades'


class CustomInstall(install):
    """Custom installation to fix script info and install man."""

    def initialize_options(self):
        """Run parent initialization and then fix the scripts var."""
        install.initialize_options(self)

        # leave the proper script according to the platform
        script = SCRIPT_WIN if sys.platform == "win32" else SCRIPT_REST
        self.distribution.scripts = [script]

    def run(self):
        """Run parent install, and then save the man file."""
        install.run(self)

        # man directory
        if self._custom_man_dir is not None:
            if not os.path.exists(self._custom_man_dir):
                os.makedirs(self._custom_man_dir)
            shutil.copy("man/fades.1", self._custom_man_dir)

    def finalize_options(self):
        """Alter the installation path."""
        install.finalize_options(self)
        if self.prefix is None:
            # no place for man page (like in a 'snap')
            man_dir = None
        else:
            man_dir = os.path.join(self.prefix, "share", "man", "man1")

            # if we have 'root', put the building path also under it (used normally
            # by pbuilder)
            if self.root is not None:
                man_dir = os.path.join(self.root, man_dir[1:])
        self._custom_man_dir = man_dir


setup(
    name='fades',
    version=get_version(),
    license='GPL-3',
    author='Facundo Batista, Nicolás Demarchi',
    author_email='facundo@taniquetil.com.ar, mail@gilgamezh.me',
    description=(
        'A system that automatically handles the virtualenvs in the cases '
        'normally found when writing scripts and simple programs, and '
        'even helps to administer big projects.'),
    long_description=open('README.rst').read(),
    url='https://github.com/PyAr/fades',
    download_url="https://github.com/PyAr/fades/releases",  # Release download URL.
    packages=["fades"],
    scripts=[SCRIPT_WIN, SCRIPT_REST],
    keywords="virtualenv utils utility scripts",  # to get found easily on PyPI results, etc.
    cmdclass={
        'install': CustomInstall,
    },
    install_requires=['setuptools'],
    tests_require=['logassert', 'pyxdg', 'pyuca', 'pytest', 'flake8',
                   'pep257', 'rst2html5'],  # what unittests require
    python_requires='>=3.3',  # Minimum Python version supported.
    extras_require={
        'pyxdg': 'pyxdg',
        'virtualenv': 'virtualenv',
        'setuptools': 'setuptools',
    },

    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',

        'Environment :: Console',

        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',

        'License :: OSI Approved :: GNU General Public License (GPL)',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

        'Natural Language :: English',
        'Natural Language :: Spanish',

        'Operating System :: MacOS',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: Implementation :: CPython',

        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
)
