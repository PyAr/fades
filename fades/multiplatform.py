# Copyright 2016-2026 Facundo Batista, Nicolás Demarchi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General
# Public License version 3, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
# For further info, check  https://github.com/PyAr/fades

"""Platform agnostic collection of utilities."""

from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl

    @contextmanager
    def filelock(filepath: Path):
        """Context manager to lock over a file using best method: fcntl."""
        with open(filepath, 'w') as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            yield
            fcntl.flock(fh, fcntl.LOCK_UN)
        try:
            filepath.unlink()
        except FileNotFoundError:
            pass

except ImportError:
    import time

    @contextmanager
    def filelock(filepath: Path):
        """Context manager to lock over a file where fcntl doesn't exist."""
        try:
            while True:
                try:
                    with open(filepath, "x"):
                        yield
                    break
                except FileExistsError:
                    time.sleep(.5)
        finally:
            try:
                filepath.unlink()
            except FileNotFoundError:
                pass
