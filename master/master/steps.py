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

else:
    mkvirtualenv = [
        "virtualenv-%s" % os.environ["PYTHON_VERSION"], virtualenv_root,
        "--quiet"]
    python_bin_name = "python"
    pip_bin_name = "pip"
    bin_dir = "bin"

# Create the virtualenv
subprocess.check_call(mkvirtualenv)

python = os.path.join(virtualenv_root, bin_dir, python_bin_name)
pip = os.path.join(virtualenv_root, bin_dir, pip_bin_name)

print(json.dumps(
    {"virtualenv": virtualenv_root, "tempdir": tempdir,
    "python": python, "pip": pip}))
""".strip()

CREATE_REQUIREMENTS = """

""".strip()

REPO_URL = "git://github.com/pyfarm/pyfarm-{project}.git"

Clone = partial(Git, clobberOnFailure=True, progress=True)


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


def clone_steps(project):
    projects = ["core"]
    steps = [
        Clone(REPO_URL.format(project="core"), workdir="core")]

    if project != "core":
        projects.append(project)
        steps.append(
            Clone(REPO_URL.format(project=project), workdir=project,
                  name="clone %s" % project))

    return projects, steps


def get_build_factory(project, platform, pyversion):
    factory = BuildFactory()

    # Git
    project_dirs, git_steps = clone_steps(project)
    factory.addSteps(git_steps)

    # Create the virtual environment
    factory.addStep(
        CreateEnvironment(
            name="create environment",
            command=["python%s" % pyversion, "-c", CREATE_ENVIRONMENT]))

    # Install 'core'
    factory.addStep(
        ShellCommand(
            name="install pyfarm.core",
            workdir="core",
            command=[Property("pip"), "install", "-e", ".", "--egg"]))

    # Install this package
    if project != "core":
        factory.addStep(
            ShellCommand(
                name="install pyfarm.%s" % project,
                workdir=project,
                command=[Property("pip"), "install", "-e", ".", "--egg"]))

    # Install test packages
    test_requirements = ["nose"]
    if not pyversion.startswith("3"):
        test_requirements.append("mock")

    factory.addStep(
        ShellCommand(
            name="install test packages",
            command=[Property("pip"), "install"] + test_requirements))

    # Destroy the virtualenv
    factory.addStep(
        RemoveDirectory(
            Property("tempdir"), flunkOnFailure=False, haltOnFailure=False))

    return factory