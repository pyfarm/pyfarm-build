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
import tempfile
import os
import signal
import socket
import subprocess
from functools import partial
from os.path import isdir, join

import virtualenv

from buildbot.process.buildstep import BuildStep, SUCCESS
from buildbot.process.factory import BuildFactory
from buildbot.steps.source.git import Git
from buildbot.steps.slave import RemoveDirectory
from buildbot.steps.shell import ShellCommand, SetPropertyFromCommand
from buildbot.steps.python_twisted import Trial
from buildbot.steps.master import MasterShellCommand
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


class MasterMakeApplication(BuildStep):
    def start(self):
        # Retrieve socket to listen on
        bind_port = None
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(("", 0))
                sock.listen(1)

            except Exception:
                continue

            else:
                _, bind_port = sock.getsockname()
                break

            finally:
                sock.close()

        tempdir = tempfile.mkdtemp()
        appdir = join(tempdir, "app")
        virtualenv_dir = join(appdir, "virtualenv")
        virtualenv.create_environment(virtualenv_dir)
        pip = join(virtualenv_dir, "bin", "pip")
        uwsgi = join(virtualenv_dir, "bin", "uwsgi")
        uwsgi_log = join(appdir, "uwsgi.log")
        uwsgi_pid = join(appdir, "uwsgi.pid")

        # Create uwsgi configuration file from template
        with open("master/uwsgi.ini.in") as uwsgi_ini:
            uwsgi_ini = uwsgi_ini.read() % dict(
                bind_port=bind_port,
                virtualenv=virtualenv_dir,
                log=uwsgi_log,
                pidfile=uwsgi_pid,
                appdir=appdir)

        # Write uwsgi configuration file
        uwsgi_ini_out = join(appdir, "uwsgi.ini")
        with open(uwsgi_ini_out, "w") as uwsgi_ini_file:
            uwsgi_ini_file.write(uwsgi_ini)

        self.setProperty("uwsgi_ini", uwsgi_ini_out)
        self.setProperty("uwsgi_pid", uwsgi_pid)
        self.setProperty("uwsgi", uwsgi)
        self.setProperty("appdir", tempdir)
        self.setProperty("master_virtualenv", virtualenv_dir)
        self.setProperty("master_pip", pip)
        self.finished(SUCCESS)


class MasterKillApplication(BuildStep):
    def start(self):
        with open(self.getProperty("uwsgi_pid")) as pid_file:
            pid = int(pid_file.read().strip())

        os.kill(pid, signal.SIGINT)
        self.finished(SUCCESS)


def get_build_factory(project, platform, pyversion, dbtype):
    factory = BuildFactory()

    pip_download_cache = "pip_cache"
    if platform == "linux":
        pip_download_cache = "/home/buildslave/.pip/cache"

    if platform == "win":
        pip_download_cache = "C:\\Users\\buildbot\\.pip\\cache"

    if platform == "mac":
        pip_download_cache = "/Users/buildbot/.pip/cache"

    # Master side setup for the agent
    if project == "agent":
        # Setup initial clones
        temproot = join(tempfile.gettempdir(), "buildbot")
        repos = join(temproot, "repos")
        repo_core = join(repos, "pyfarm-core", pyversion)
        repo_master = join(repos, "pyfarm-master", pyversion)

        # Pull or create core repo
        if not isdir(repo_core):
            subprocess.check_call([
                "git", "clone",
                REPO_URL.format(project="core"), repo_core])
        else:
            subprocess.check_call([
                "git", "reset", "--hard", "origin/master"], cwd=repo_core)
            subprocess.check_call(["git", "pull"], cwd=repo_core)

        # Pull or create master repo
        if not isdir(repo_master):
            subprocess.check_call([
                "git", "clone",
                REPO_URL.format(project="master"), repo_master])
        else:
            subprocess.check_call([
                "git", "reset", "--hard", "origin/master"], cwd=repo_master)
            subprocess.check_call(["git", "pull"], cwd=repo_master)

        factory.addStep(MasterMakeApplication(name="make application"))

        # Every test run should reset the repos and pull
        for path in (repo_core, repo_master):
            factory.addStep(
                MasterShellCommand(
                    ["git", "reset", "--hard", "origin/master"],
                    path=path, name="git reset %s" % path))
            factory.addStep(
                MasterShellCommand(
                    ["git", "pull"],
                    path=path, name="git pull %s" % path))
            factory.addStep(
                MasterShellCommand(
                    [Property("master_pip"), "install", path],
                    name="install %s" % path))
        factory.addStep(
            MasterShellCommand(
                [Property("master_pip"), "install", "uwsgi"],
                name="install uwsgi"))

        factory.addStep(
            MasterShellCommand(
                [Property("uwsgi"), Property("uwsgi_ini")],
                name="run uwsgi"))

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
    if project != "agent":
        requirements = ["nose"]
    else:
        requirements = []

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
            "mysql+mysqlconnector://buildbot:42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2@10.8.0.1/%s" % db_name)

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
    else:
        factory.addStep(Trial(tests="agent.tests"))

    # Destroy the virtualenv on the remote host
    factory.addStep(
        RemoveDirectory(
            Property("tempdir"), flunkOnFailure=False, haltOnFailure=False))

    if project == "agent":
        factory.addStep(
            MasterKillApplication(name="kill uwsgi"))

        factory.addStep(
            MasterShellCommand(["rm", "-rfv", Property("appdir")],
                               name="remove appdir"))

    return factory
