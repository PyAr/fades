Enabling the uv backend by default
==================================

To always use the uv backend you need ``use_uv=true`` in the ``[fades]`` section of a
fades config file (see "Setting options using config files" in the README).

If you prefer not to edit the file by hand, this command adds it to your user's config
file (creating it if needed)::

    python -W ignore -c "import configparser; from pathlib import Path; from fades.helpers import get_confdir; \
    p = Path(get_confdir()) / 'fades.ini'; c = configparser.ConfigParser(); c.read(p); \
    c.has_section('fades') or c.add_section('fades'); c.set('fades', 'use_uv', 'true'); \
    c.write(p.open('w')); print('uv enabled by default in', p)"

Note it needs fades to be importable by that ``python`` (e.g. if fades was installed with
``pip``); otherwise just add the line to the file yourself.
