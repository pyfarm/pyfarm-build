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
from buildbot.schedulers.basic import SingleBranchScheduler
from buildbot.changes.filter import ChangeFilter
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


def get_hosts(config_data):
    """Pulls slaves from the provided configuration data"""
    slaves = config_data["slaves"]

    for host_group in ("persistent", "aws"):
        for name, data in slaves[host_group].items():
            if not data.pop("enabled", True):
                print >> sys.stderr, "Slave %s is not enabled" % name
                continue

            host_type = data.pop("type")
            projects = data.pop("projects")
            for project, python_versions in projects.items():
                for python_version in python_versions:
                    yield (
                        host_group, host_type, name, project,
                        str(python_version), data.copy())


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
builder_slaves = {}
scheduler_groups = {}

# Create slaves
for type_, platform, name, slave_project, python_version, slavecfg in \
        get_hosts(file_cfg):
    if type_ == "persistent":
        slave = BuildSlave(name, slavecfg.pop("passwd"), **slavecfg)
    elif type_ == "aws":
        slave = EC2LatentBuildSlave(
            name, slavecfg.pop("passwd"), slavecfg.pop("instance_type"),
            **slavecfg)
    else:
        raise NotImplementedError("Cannot handle host type %s" % type_)

    if slave_project == "master":
        for dbtype in ("postgres", "mysql"):
            builder_name = "{slave_project}-{dbtype}-{platform}-" \
                           "{python_version}".format(
                slave_project=slave_project, dbtype=dbtype, platform=platform,
                python_version=python_version)
            builder_slaves.setdefault(builder_name, [])
            builder_slaves[builder_name].append(name)
            slaves.append(slave)
            scheduler_group = scheduler_groups.setdefault(slave_project, set())
            scheduler_group.add(builder_name)
    else:
        builder_name = "{slave_project}-{platform}-{python_version}".format(
            slave_project=slave_project, platform=platform,
            python_version=python_version)
        builder_slaves.setdefault(builder_name, [])
        builder_slaves[builder_name].append(name)
        slaves.append(slave)

        scheduler_group = scheduler_groups.setdefault(slave_project, set())
        scheduler_group.add(builder_name)


from functools import partial


def filter_change(change, group=None):
    assert group is not None
    return group in change.repository

print scheduler_groups
for scheduler_group, scheduler_builders in scheduler_groups.items():
    scheduler = SingleBranchScheduler(
        scheduler_group,
        builderNames=list(scheduler_builders),
        change_filter=ChangeFilter(
            filter_fn=partial(filter_change, group=scheduler_group))
    )
    schedulers.append(scheduler)

for name, slaves in builder_slaves.items():
    try:
        project, platform, python_version = name.split("-")
        dbtype = None
    except ValueError:
        project, dbtype, platform, python_version = name.split("-")

    # Create builder
    builder = BuilderConfig(
        env={"PYTHON_VERSION": python_version},
        name=name, slavenames=slaves,
        factory=get_build_factory(project, platform, python_version, dbtype))
    builders.append(builder)

    # Create scheduler for this builder
    schedulers.append(
        Triggerable(name=name, builderNames=[name]))
    schedulers.append(
        ForceScheduler("%s-force" % name, builderNames=[name]))


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
    auth=BasicAuth(file_cfg["authz_users"]),
    **file_cfg["authz_perms"])

web_status = WebStatus(http_port=file_cfg["protocols"]["web"], authz=authz)
status.append(web_status)
