#!/usr/bin/env python3.4

# Copyright 2014, 2015 Facundo Batista, Nicolás Demarchi
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

    python3.4
    python3-xdg   (optional)
    python3-pkg-resources
    python3-setuptools
"""

import os
import re
import shutil

from distutils.core import setup
from setuptools.command.install import install


def get_version():
    """Retrieves package version from the file."""
    with open('fades/_version.py') as fh:
        m = re.search("'([^']*)'", fh.read())
    if m is None:
        raise ValueError("Unrecognized version in 'fades/_version.py'")
    return m.groups()[0]


class CustomInstall(install):
    """Custom installation to fix script info and install man."""

    def run(self):
        """Run parent install, and then save the man file."""
        install.run(self)

        # man directory
        if not os.path.exists(self._custom_man_dir):
            os.makedirs(self._custom_man_dir)
        shutil.copy("man/fades.1", self._custom_man_dir)

    def finalize_options(self):
        """Alter the installation path."""
        install.finalize_options(self)
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

    packages=["fades"],
    scripts=["bin/fades"],

    cmdclass={
        'install': CustomInstall,
    },
    install_requires=['setuptools'],
    extras_require={
        'pyxdg': 'pyxdg',
        'virtualenv': 'virtualenv',
        'setuptools': 'setuptools',
    }
)
