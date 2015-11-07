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
import shutil

from setuptools.command.install import install
from distutils.core import setup

# get the version from the file
version = open('version.txt').read().strip()


class CustomInstall(install):
    """Custom installation to fix script info and install man."""

    def run(self):
        """Run parent install, and then save the install dir in the script."""
        install.run(self)

        # fix installation path in the script(s)
        for script in self.distribution.scripts:
            script_path = os.path.join(self.install_scripts, os.path.basename(script))
            with open(script_path, 'rt', encoding='utf8') as fh:
                content = fh.read()
            content = content.replace('@ INSTALLED_BASE_DIR @', self.install_lib)
            content = content.replace('@ VERSION @', version)
            with open(script_path, 'wt', encoding='utf8') as fh:
                fh.write(content)

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
    version=version,
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
    package_data={
        "": ["version.txt"],
    },
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
