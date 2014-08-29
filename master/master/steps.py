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
from buildbot.process.properties import Property

CREATE_ENVIRONMENT = """
from __future__ import print_function
import os
import json
import tempfile
import subprocess
tempdir = tempfile.mkdtemp()
virtualenv = os.path.join(tempdir, "virtualenv")
make_virtualenv = ["virtualenv", virtualenv, "--quiet"]

# Windows requires the site-packages directory so we can access things
# like pywin32
if os.name == "nt":
    virtualenv.append("--system-site-packages")
    bin_dir = "Scripts"
    activate_script = "activate.bat"
else:
    bin_dir = "bin"
    activate_script = "activate"

# Create the virtualenv
subprocess.check_call(make_virtualenv)

activate = os.path.join(virtualenv, bin_dir, activate_script)
print(json.dumps(
    {"virtualenv": virtualenv, "activate": activate, "tempdir": tempdir}))
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
        steps.append(Clone(REPO_URL.format(project=project), workdir=project))

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

    # Destroy the virtualenv
    factory.addStep(
        RemoveDirectory(
            Property("tempdir"), flunkOnFailure=False, haltOnFailure=False))

    return factory