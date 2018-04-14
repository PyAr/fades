

"""Tiny tool to autogenerate random 'venvs.idx' content for testing purposes."""


import os
from random import randint
from uuid import uuid4
from shutil import which
import datetime
import json


def main():
    """Build a valid random-ish Fades venvs.idx content."""
    y3ar, h0me = datetime.date.today().year, os.path.join(os.path.expanduser("~"), ".fades")
    venvs_idx = ""
    for _ in range(randint(2, 9)):
        random_envpath = os.path.join(h0me, str(uuid4()))
        random_timestamp = int(datetime.datetime(year=randint(2000, y3ar),
                                                 month=randint(1, 12),
                                                 day=randint(1, 28)).timestamp())
        venvs_idx += json.dumps({
            "timestamp": random_timestamp,
            "installed": {},
            "metadata": {
                "env_path": random_envpath,
                "env_bin_path": os.path.join(random_envpath, "bin"),
                "pip_installed": True
            },
            "interpreter": which("python3") or "/usr/bin/python3.6",
            "options": {
                "pyvenv_options": [],
                "virtualenv_options": []
            }
        }) + "\n"
    print(venvs_idx.strip())
    return venvs_idx.strip()


if __name__ in "__main__":
    main()
