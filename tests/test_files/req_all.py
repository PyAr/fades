# -*- coding: utf-8 -*-
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
fades:
    foo==1.4
"""


class FooClass():
    """Create always a virtualenv.
    requirements for fades:
    bar>1.8.9
    """
    def __init__(self):
        pass

    def create(self, interpreter):
        """
        Create a virtualenv using the virtualenv lib.
        fades:
        more>1.6
        """
        print("create")
