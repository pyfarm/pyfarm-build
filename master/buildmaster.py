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

import logging
import sys
from collections import Mapping

import yaml
from buildbot.buildslave import BuildSlave
from buildbot.buildslave.ec2 import EC2LatentBuildSlave
from buildbot.schedulers.forcesched import ForceScheduler
from buildbot.changes.pb import PBChangeSource
from buildbot.config import BuilderConfig
from buildbot.schedulers.triggerable import Triggerable
from buildbot.status.html import WebStatus
from buildbot.status.web.auth import BasicAuth
from buildbot.status.web.authz import Authz
from twisted.web.server import Site
from twisted.internet import reactor

from master.changesource import GitHubBuildBot
from master.steps import get_build_factory


def update(d, u):
    for k, v in u.iteritems():
        if isinstance(v, Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d

# Load public configuration
with open("config.yml", "r") as public_yaml_file:
    public_config = yaml.load(public_yaml_file)

# Load private configuration
with open("private.yml", "r") as private_yaml_file:
    private_config = yaml.load(private_yaml_file)

# Merge the configurations
file_cfg = update(public_config, private_config)

# Main configuration read in the .tac file
config = BuildmasterConfig = {
    "title": "PyFarm",
    "titleURL": "https://build.pyfarm.net",
    "buildbotURL": "http://127.0.0.1:8010",
    "db_url": file_cfg["db"],
    "status": [],
    "slaves": [],
    "builders": [],
    "schedulers": [],
    "change_source": [
        PBChangeSource(
            user=file_cfg["changesource"]["user"],
            passwd=file_cfg["changesource"]["passwd"])
    ],
    "protocols": {
        "pb": {"port": file_cfg["protocols"]["pb"]}
    }
}

projects = ("core", "agent", "master")
builders = config["builders"]
status = config["status"]
schedulers = config["schedulers"]
change_source = config["change_source"]
slaves = config["slaves"]
slave_data = []

# Add persistent build slave(s)
for name, cfg in file_cfg["slaves"]["persistent"].items():
    if not cfg.pop("enabled"):
        continue

    slave_data.append((name, cfg.pop("type"), map(str, cfg.pop("python"))))
    slaves.append(BuildSlave(name, cfg.pop("passwd"), **cfg))

# Add aws build slaves
for name, cfg in file_cfg["slaves"]["aws"].items():
    if not cfg.pop("enabled"):
        continue

    slave_data.append((name, cfg.pop("type"), map(str, cfg.pop("python"))))
    slaves.append(EC2LatentBuildSlave(
        name, cfg.pop("passwd"), cfg.pop("instance_type"), **cfg))

builder_names = []
for project in projects:
    project_builders = []
    for slave, platform, python_versions in slave_data:
        for python_version in python_versions:
            name = "{project}-{platform}-{python_version}".format(**locals())
            builder = BuilderConfig(
                env={"PYTHON_VERSION": python_version},
                name=name, slavename=slave,
                factory=get_build_factory(project, platform, python_version))
            builders.append(builder)
            builder_names.append(name)
            project_builders.append(name)
    scheduler = Triggerable(name=project, builderNames=project_builders)
    schedulers.append(scheduler)
    schedulers.append(
        ForceScheduler("%s-force" % project, builderNames=project_builders))

# Setup the github hook
github_bot = GitHubBuildBot()
github_bot.github = file_cfg["changesource"]["github"]["host"]
github_bot.master = file_cfg["changesource"]["github"]["master"]
github_bot.secret = file_cfg["changesource"]["github"]["secret"]
github_bot.auth = ":".join([
    file_cfg["changesource"]["user"], file_cfg["changesource"]["passwd"]])

# Get the reactor to listen for the commit hook
reactor.listenTCP(file_cfg["changesource"]["github"]["port"], Site(github_bot))

# Logging setup (mainly used by the github hook)
if file_cfg["log_level"]:
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(stream=sys.stdout)],
        level=logging._levelNames[file_cfg["log_level"].upper()])


# Web interface auth
authz = Authz(
    auth=BasicAuth(file_cfg["http_users"]),
    gracefulShutdown="auth",
    forceBuild="auth",
    forceAllBuilds="auth",
    pingBuilder="auth",
    stopBuild="auth",
    stopAllBuilds="auth",
    cancelPendingBuild="auth")

web_status = WebStatus(http_port=file_cfg["protocols"]["web"], authz=authz)
status.append(web_status)