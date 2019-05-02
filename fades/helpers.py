# Copyright 2014-2015 Facundo Batista, Nicolás Demarchi
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

"""A collection of utilities for fades."""

import os
import sys
import json
import logging
import subprocess
import tempfile

from urllib import request, parse
from urllib.error import HTTPError

import pkg_resources

from fades import FadesError, HTTP_STATUS_NOT_FOUND, HTTP_STATUS_OK, _version

logger = logging.getLogger(__name__)

# command to retrieve the version from an external Python
SHOW_VERSION_CMD = """
import sys, json
d = dict(path=sys.executable)
d.update(zip('major minor micro releaselevel serial'.split(), sys.version_info))
print(json.dumps(d))
"""

# the url to query PyPI for project versions
BASE_PYPI_URL = 'https://pypi.org/pypi/{name}/json'
BASE_PYPI_URL_WITH_VERSION = 'https://pypi.org/pypi/{name}/{version}/json'

# prefix for all stdout lines when running a command
STDOUT_LOG_PREFIX = ":: "

# env var name provided by snappy where process can read/write; this path already includes
# 'fades' in it, it's a different dir for each user, and accessable by different versions of fades
SNAP_BASEDIR_NAME = 'SNAP_USER_COMMON'


class ExecutionError(Exception):
    """Execution of subprocess ended not in 0."""

    def __init__(self, retcode, cmd, collected_stdout):
        """Init."""
        self._retcode = retcode
        self._cmd = cmd
        self._collected_stdout = collected_stdout
        super().__init__()

    def dump_to_log(self, logger):
        """Send the cmd info and collected stdout to logger."""
        logger.error("Execution ended in %s for cmd %s", self._retcode, self._cmd)
        for line in self._collected_stdout:
            logger.error(STDOUT_LOG_PREFIX + line)


def logged_exec(cmd):
    """Execute a command, redirecting the output to the log."""
    logger = logging.getLogger('fades.exec')
    logger.debug("Executing external command: %r", cmd)
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    stdout = []
    for line in p.stdout:
        line = line[:-1]
        stdout.append(line)
        logger.debug(STDOUT_LOG_PREFIX + line)
    retcode = p.wait()
    if retcode:
        raise ExecutionError(retcode, cmd, stdout)
    return stdout


def _get_basedirectory():
    from xdg import BaseDirectory
    return BaseDirectory


def _get_specific_dir(dir_type):
    """Get a specific directory, using some XDG base, with sensible default."""
    if SNAP_BASEDIR_NAME in os.environ:
        logger.debug("Getting base dir information from SNAP_BASEDIR_NAME env var.")
        direct = os.path.join(os.environ[SNAP_BASEDIR_NAME], dir_type)
    else:
        try:
            basedirectory = _get_basedirectory()
        except ImportError:
            logger.debug("Using last resort base dir: ~/.fades")
            from os.path import expanduser
            direct = os.path.join(expanduser("~"), ".fades")
        else:
            xdg_attrib = 'xdg_{}_home'.format(dir_type)
            base = getattr(basedirectory, xdg_attrib)
            direct = os.path.join(base, 'fades')

    if not os.path.exists(direct):
        os.makedirs(direct)
    return direct


def get_basedir():
    """Get the base fades directory, from xdg or kinda hardcoded."""
    return _get_specific_dir('data')


def get_confdir():
    """Get the config fades directory, from xdg or kinda hardcoded."""
    return _get_specific_dir('config')


def _get_interpreter_info(interpreter=None):
    """Return the interpreter's full path using pythonX.Y format."""
    if interpreter is None:
        # If interpreter is None by default returns the current interpreter data.
        major, minor = sys.version_info[:2]
        executable = sys.executable
    else:
        args = [interpreter, '-c', SHOW_VERSION_CMD]
        try:
            requested_interpreter_info = logged_exec(args)
        except Exception as error:
            logger.error("Error getting requested interpreter version: %s", error)
            raise FadesError("Could not get interpreter version")
        requested_interpreter_info = json.loads(requested_interpreter_info[0])
        executable = requested_interpreter_info['path']
        major = requested_interpreter_info['major']
        minor = requested_interpreter_info['minor']
    if executable[-1].isdigit():
        executable = executable.split(".")[0][:-1]
    interpreter = "{}{}.{}".format(executable, major, minor)
    return interpreter


def get_interpreter_version(requested_interpreter):
    """Return a 'sanitized' interpreter and indicates if it is the current one."""
    logger.debug('Getting interpreter version for: %s', requested_interpreter)
    current_interpreter = _get_interpreter_info()
    logger.debug('Current interpreter is %s', current_interpreter)
    if requested_interpreter is None:
        return(current_interpreter, True)
    else:
        requested_interpreter = _get_interpreter_info(requested_interpreter)
        is_current = requested_interpreter == current_interpreter
        logger.debug('Interpreter=%s. It is the same as fades?=%s',
                     requested_interpreter, is_current)
        return (requested_interpreter, is_current)


def get_latest_version_number(project_name):
    """Return latest version of a package."""
    try:
        raw = request.urlopen(BASE_PYPI_URL.format(name=project_name)).read()
    except HTTPError as error:
        logger.warning("Network error. Error: %s", error)
        raise error
    try:
        data = json.loads(raw.decode("utf8"))
        latest_version = data["info"]["version"]
        return latest_version
    except (KeyError, ValueError) as error:  # malformed json or empty string
        logger.error("Could not get the version of the package. Error: %s", error)
        raise error


def check_pypi_updates(dependencies):
    """Return a list of dependencies to upgrade."""
    dependencies_up_to_date = []
    for dependency in dependencies.get('pypi', []):
        # get latest version from PyPI api
        try:
            latest_version = get_latest_version_number(dependency.project_name)
        except Exception as error:
            logger.warning("--check-updates command will be aborted. Error: %s", error)
            return dependencies
        # get required version
        required_version = None
        if dependency.specs:
            _, required_version = dependency.specs[0]

        if required_version:
            dependencies_up_to_date.append(dependency)
            if latest_version > required_version:
                logger.info("There is a new version of %s: %s",
                            dependency.project_name, latest_version)
            elif latest_version < required_version:
                logger.warning("The requested version for %s is greater "
                               "than latest found in PyPI: %s",
                               dependency.project_name, latest_version)
            else:
                logger.info("The requested version for %s is the latest one in PyPI: %s",
                            dependency.project_name, latest_version)
        else:
            project_name_plus = "{}=={}".format(dependency.project_name, latest_version)
            dependencies_up_to_date.append(pkg_resources.Requirement.parse(project_name_plus))
            logger.info("The latest version of %r is %s and will use it.",
                        dependency.project_name, latest_version)

    dependencies["pypi"] = dependencies_up_to_date
    return dependencies


def _pypi_head_package(dependency):
    """Hit pypi with a http HEAD to check if pkg_name exists."""
    if dependency.specs:
        _, version = dependency.specs[0]
        url = BASE_PYPI_URL_WITH_VERSION.format(name=dependency.project_name, version=version)
    else:
        url = BASE_PYPI_URL.format(name=dependency.project_name)
    logger.debug("Doing HEAD requests against %s", url)
    req = request.Request(url, method='HEAD')
    try:
        response = request.urlopen(req)
    except HTTPError as http_error:
        if http_error.code == HTTP_STATUS_NOT_FOUND:
            return False
        else:
            raise
    if response.status == HTTP_STATUS_OK:
        logger.debug("%r exists in PyPI.", dependency)
        return True
    else:
        # Maybe we are getting somethink like a redirect. In this case we are only
        # warning to the user and trying to install the dependency.
        # In the worst scenery fades will fail to install it.
        logger.warning("Got a (unexpected) HTTP_STATUS=%r and reason=%r checking if %r exists",
                       response.status, response.reason, dependency)
        return True


def check_pypi_exists(dependencies):
    """Check if the indicated dependencies actually exists in pypi."""
    for dependency in dependencies.get('pypi', []):
        logger.debug("Checking if %r exists in PyPI", dependency)
        try:
            exists = _pypi_head_package(dependency)
        except Exception as error:
            logger.error("Error checking %s in PyPI: %r", dependency, error)
            raise FadesError("Could not check if dependency exists in PyPI")
        else:
            if not exists:
                logger.error("%s doesn't exists in PyPI.", dependency)
                return False
    return True


class _ScriptDownloader:
    """Grouping of different backends downloaders."""

    # a user-agent for hitting the network
    USER_AGENT = "fades/{} (https://github.com/PyAr/fades/)".format(_version.__version__)
    HEADERS_PLAIN = {
        'Accept': 'text/plain',
        'User-Agent': USER_AGENT,
    }
    HEADERS_JSON = {
        'Accept': 'application/json',
        'User-Agent': USER_AGENT,
    }

    # simple network locations to name map
    NETLOCS = {
        'linkode.org': 'linkode',
        'pastebin.com': 'pastebin',
        'gist.github.com': 'gist',
    }

    def __init__(self, url):
        """Init."""
        self.url = url
        self.name = self._decide()

    def _decide(self):
        """Find out which method should be applied to download that URL."""
        netloc = parse.urlparse(self.url).netloc
        name = self.NETLOCS.get(netloc, 'raw')
        return name

    def get(self):
        """Get the script content from the URL using the decided downloader."""
        method_name = "_download_" + self.name
        method = getattr(self, method_name)
        return method()

    def _download_raw(self, url=None):
        """Download content from URL directly."""
        if url is None:
            url = self.url
        req = request.Request(url, headers=self.HEADERS_PLAIN)
        resp = request.urlopen(req)

        # check if the response url is different than the original one; in this case we had
        # redirected, and we need to pass the new url response through the proper
        # pastebin-dependant adapter, so recursively go into another _ScriptDownloader
        if resp.geturl() != url:
            new_url = resp.geturl()
            downloader = _ScriptDownloader(new_url)
            logger.info(
                "Download redirect detect, now downloading from %r using %r downloader",
                new_url, downloader.name)
            return downloader.get()

        # simple non-redirect response
        return resp.read().decode("utf8")

    def _download_linkode(self):
        """Download content from Linkode pastebin."""
        # build the API url
        linkode_id = self.url.split("/")[-1]
        if linkode_id.startswith("#"):
            linkode_id = linkode_id[1:]
        url = "https://linkode.org/api/1/linkodes/" + linkode_id

        req = request.Request(url, headers=self.HEADERS_JSON)
        resp = request.urlopen(req)
        raw = resp.read()
        data = json.loads(raw.decode("utf8"))
        content = data['content']
        return content

    def _download_pastebin(self):
        """Download content from Pastebin itself."""
        paste_id = self.url.split("/")[-1]
        url = "https://pastebin.com/raw/" + paste_id
        return self._download_raw(url)

    def _download_gist(self):
        """Download content from github's pastebin."""
        parts = parse.urlparse(self.url)
        url = "https://gist.github.com" + parts.path + "/raw"
        return self._download_raw(url)


def download_remote_script(url):
    """Download the content of a remote script to a local temp file."""
    temp_fh = tempfile.NamedTemporaryFile('wt', encoding='utf8', suffix=".py", delete=False)
    downloader = _ScriptDownloader(url)
    logger.info(
        "Downloading remote script from %r (using %r downloader) to %r",
        url, downloader.name, temp_fh.name)

    content = downloader.get()
    temp_fh.write(content)
    temp_fh.close()
    return temp_fh.name
