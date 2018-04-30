"""Init file to allow execution of fades as a module."""

import sys

from fades import main

try:
    rc = main.go()
except Exception:
    sys.exit(-1)

sys.exit(rc)
