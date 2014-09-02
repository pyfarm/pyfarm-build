# No shebang line, this module is meant to be imported
#
# Copyright 2014 Oliver Palmer
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from functools import partial

from buildbot.process.factory import BuildFactory
from buildbot.steps.source.git import Git
from buildbot.steps.shell import SetPropertyFromCommand
from buildbot.steps.slave import RemoveDirectory
from buildbot.steps.shell import ShellCommand
from buildbot.process.properties import Property

CREATE_ENVIRONMENT = """
from __future__ import print_function
import os
import json
import tempfile
import subprocess

tempdir = tempfile.mkdtemp()
virtualenv_root = os.path.join(tempdir, "virtualenv")
short_pyversion = os.environ["PYTHON_VERSION"].replace(".", "")

# Windows requires the site-packages directory so we can access things
# like pywin32
if os.name == "nt":
    mkvirtualenv = [
        "C:\\Python%s\\Scripts\\virtualenv.exe" % short_pyversion,
        virtualenv_root, "--system-site-packages", "--quiet"]
    python_bin_name = "python.exe"
    pip_bin_name = "pip.exe"
    bin_dir = "Scripts"
    nose_bin_name = "nosetests.exe"

else:
    mkvirtualenv = [
        "virtualenv-%s" % os.environ["PYTHON_VERSION"], virtualenv_root,
        "--quiet"]
    python_bin_name = "python"
    pip_bin_name = "pip"
    bin_dir = "bin"
    nose_bin_name = "nosetests"

# Create the virtualenv
subprocess.check_call(mkvirtualenv)

print(json.dumps(
    {"virtualenv": virtualenv_root, "tempdir": tempdir,
    "python": os.path.join(virtualenv_root, bin_dir, python_bin_name),
    "pip": os.path.join(virtualenv_root, bin_dir, pip_bin_name),
    "nosetests": os.path.join(virtualenv_root, bin_dir, nose_bin_name)}))
""".strip()

CREATE_REQUIREMENTS = """

""".strip()

REPO_URL = "https://github.com/pyfarm/pyfarm-{project}"

Clone = partial(Git, clobberOnFailure=True, progress=True, mode='full')


class CreateEnvironment(SetPropertyFromCommand):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("extract_fn", self._extract_fn)
        SetPropertyFromCommand.__init__(self, *args, **kwargs)

    def _extract_fn(self, _, stdout, stderr):
        data = json.loads(stdout)
        for key, value in data.items():
            if isinstance(value, unicode):
                data[key] = str(value)
        return data


def get_build_factory(project, platform, pyversion, dbtype):
    factory = BuildFactory()

    pip_download_cache = "pip_cache"
    if platform == "linux":
        pip_download_cache = "/home/buildbot/pip_cache"

    if platform == "win":
        pip_download_cache = "C:\\Users\\buildbot\\pip_cache"

    if platform == "mac":
        pip_download_cache = "/Users/buildbot/pip_cache"

    # Git
    factory.addStep(
        Clone(REPO_URL.format(project=project), workdir=project,
        name="clone %s" % project))

    # Create the virtual environment
    factory.addStep(
        CreateEnvironment(
            name="create environment",
            command=["python%s" % pyversion, "-c", CREATE_ENVIRONMENT]))

    # Install this package
    factory.addStep(
        ShellCommand(
            name="install pyfarm.%s" % project,
            workdir=project,
            env={"PIP_DOWNLOAD_CACHE": pip_download_cache},
            command=[Property("pip"), "install", "-e", ".", "--egg"]))

    # Install test packages
    requirements = ["nose"]
    env = {}
    if not pyversion.startswith("3."):
        requirements.append("mock")

    if pyversion == "2.6":
        requirements.append("unittest2")

    db_name = "pyfarm_unittest_%s_%s" % (platform, pyversion.replace(".", ""))
    print "testdb: %s" % db_name

    if dbtype == "mysql":
        requirements.append("mysql-connector-python")
        env.update(
            DATABASE_NAME=db_name,
            PYFARM_DATABASE_URI=
            "mysql+mysqlconnector://buildbot:42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2@127.0.0.1/%s" % db_name)

    if dbtype == "postgres":
        requirements.append("psycopg2")
        env.update(
            DATABASE_NAME=db_name,
            PYFARM_DATABASE_URI=
            "postgresql+psycopg2://buildbot:42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2@127.0.0.1/%s" % db_name)

    factory.addStep(
        ShellCommand(
            name="install additional packages",
            env={"PIP_DOWNLOAD_CACHE": pip_download_cache},
            command=[
                Property("pip"), "install", "--allow-external",
                "mysql-connector-python"] + requirements))

    if project in ("core", "master"):
        # TODO: configure db
        factory.addStep(
            ShellCommand(
                name="run tests",
                workdir=project,
                env=env,
                command=[Property("nosetests"), "tests", "-s", "--verbose"]))

    # Destroy the virtualenv
    factory.addStep(
        RemoveDirectory(
            Property("tempdir"), flunkOnFailure=False, haltOnFailure=False))

    return factory