# Copyright 2014 Facundo Batista, Nicolás Demarchi
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
"""
Extended class from EnvBuilder to create a venv using a uuid4 id.

NOTE: this class only work in the same python version that Fades is
running. So, you don't need to have installed a virtualenv tool. For
other python versions Fades needs a virtualenv tool installed.
"""


class FooClass():
    """Create always a virtualenv.
    requirements for fades:
    foo==1.7
    """
    def __init__(self):
        pass

    def create(self, interpreter):
        """
        Create a virtualenv using the virtualenv lib.
        fades:
        bar<1.5
        """
        print("create")
