"""Init file to allow execution of fades as a module."""

import sys

from fades import main, FadesError

try:
    rc = main.go()
except FadesError:
    sys.exit(-1)

sys.exit(rc)
