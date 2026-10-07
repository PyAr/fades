#!/usr/bin/env python3

# Copyright 2014-2026 Facundo Batista, Nicolás Demarchi
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

"""Shim over the declarative pyproject.toml, only for the man page.

All the packaging metadata lives in ``pyproject.toml``. The single thing that
cannot be expressed there is installing the man page under
``<prefix>/share/man/man1`` (there is no PEP 621 mechanism for ``data_files``,
and modern setuptools rejects it in ``pyproject.toml``). That's the only reason
this file still exists; it is consumed by ``pip``, the Debian ``pybuild`` flow
and the snap build.
"""

from setuptools import setup

setup(data_files=[("share/man/man1", ["man/fades.1"])])
