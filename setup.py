#!/usr/bin/env python3.4

# Copyright 2014 Facundo Batista, Nicolás Demarchi
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
"""

import os
import shutil

from setuptools.command.install import install
from distutils.core import setup


class CustomInstall(install):
    """Custom installation class on package files.

    It copies all the files into the "PREFIX/share/PROJECTNAME" dir.
    """
    def run(self):
        """Run parent install, and then save the install dir in the script."""
        install.run(self)

        # fix installation path in the script(s)
        for script in self.distribution.scripts:
            script_path = os.path.join(self.install_scripts, os.path.basename(script))
            with open(script_path, 'rt', encoding='utf8') as fh:
                content = fh.read()
            content = content.replace('@ INSTALLED_BASE_DIR @',
                                      self._custom_data_dir)
            with open(script_path, 'wt', encoding='utf8') as fh:
                fh.write(content)

        # man directory
        if not os.path.exists(self._custom_man_dir):
            os.makedirs(self._custom_man_dir)
        shutil.copy("man/fades.1", self._custom_man_dir)

        # version file
        shutil.copy("version.txt", self.install_lib)

    def finalize_options(self):
        """Alter the installation path."""
        install.finalize_options(self)

        # the data path is under 'prefix'
        data_dir = os.path.join(self.prefix, "share",
                                self.distribution.get_name())
        man_dir = os.path.join(self.prefix, "share", "man", "man1")

        # if we have 'root', put the building path also under it (used normally
        # by pbuilder)
        if self.root is None:
            build_dir = data_dir
        else:
            build_dir = os.path.join(self.root, data_dir[1:])
            man_dir = os.path.join(self.root, man_dir[1:])

        # change the lib install directory so all package files go inside here
        self.install_lib = build_dir

        # save this custom data dir to later change the scripts
        self._custom_data_dir = data_dir
        self._custom_man_dir = man_dir


LONG_DESCRIPTION = (
    'A system that automatically handles the virtualenvs in the simple '
    'cases normally found when writing scripts or simple programs.'
)

setup(
    name='fades',
    version=open('version.txt').read().strip(),
    license='GPL-3',
    author='Facundo Batista, Nicolás Demarchi',
    author_email='facundo@taniquetil.com.ar, mail@gilgamezh.me',
    description='FAst DEpendencies for Scripts.',
    long_description=LONG_DESCRIPTION,
    url='https://github.com/PyAr/fades',

    packages=["fades"],
    package_data={
        "": ["version.txt"],
    },
    scripts=["bin/fades"],

    cmdclass={
        'install': CustomInstall,
    },
)
