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

from functools import partial

from buildbot.process.factory import BuildFactory
from buildbot.steps.source.git import Git
from buildbot.steps.shell import SetPropertyFromCommand, ShellCommand
from buildbot.steps.slave import RemoveDirectory
from buildbot.process.properties import Property

CREATE_VIRTUALENV_DIR = """
import tempfile
print tempfile.mkdtemp(prefix="virtualenv-")
""".strip()

REPO_URL = "git://github.com/pyfarm/pyfarm-{project}.git"

Clone = partial(Git, clobberOnFailure=True, progress=True)


def clone_steps(project):
    projects = ["core"]
    steps = [
        Clone(REPO_URL.format(project="core"), workdir="core")]

    if project != "core":
        projects.append(project)
        steps.append(Clone(REPO_URL.format(project=project), workdir=project))

    return projects, steps


def create_virtualenv(platform, pyversion):
    if platform == "windows":
        venv = "C:\\Python%s\\Scripts\\virtualenv-%s" % (
            pyversion.replace(".", ""), pyversion)
        command = [venv, "--system-site-packages", Property("virtualenv")]

    else:
        venv = "virtualenv-%s" % pyversion
        command = [venv, Property("virtualenv")]

    return ShellCommand(
        name="create virtualenv",
        command=command)


def get_build_factory(project, platform, pyversion):
    factory = BuildFactory()

    # Git
    project_dirs, git_steps = clone_steps(project)
    factory.addSteps(git_steps)

    # Create the virtual environment
    factory.addStep(
        SetPropertyFromCommand(
            name="create virtualenv directory",
            property="virtualenv",
            command=["python", "-c", CREATE_VIRTUALENV_DIR]))
    factory.addStep(
        create_virtualenv(platform, pyversion))

    # Destroy the virtualenv
    factory.addStep(
        RemoveDirectory(
            Property("virtualenv"), flunkOnFailure=False, haltOnFailure=False))

    return factory