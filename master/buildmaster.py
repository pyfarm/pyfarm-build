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

from collections import Mapping

import yaml
from buildbot.buildslave import BuildSlave
from buildbot.buildslave.ec2 import EC2LatentBuildSlave
from buildbot.config import BuilderConfig
from buildbot.schedulers.triggerable import Triggerable
from buildbot.status.web import authz, auth
from buildbot.status import html

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
    "protocols": {
        "pb": {"port": 9989}
    },
    "change_source": [
        GitHubBuildBot(file_cfg["github_changesource"]["secret"])
    ]
}

projects = ("core", "agent", "master")
builders = config["builders"]
schedulers = config["schedulers"]
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
                name=name, slavename=slave,
                factory=get_build_factory(project, platform, python_version))
            builders.append(builder)
            builder_names.append(name)
            project_builders.append(name)
    scheduler = Triggerable(name=project, builderNames=project_builders)
    schedulers.append(scheduler)

#
# ####### SCHEDULERS
#
# # Configure the Schedulers, which decide how to react to incoming changes.  In this
# # case, just kick off a 'runtests' build
#
# from buildbot.schedulers.basic import SingleBranchScheduler
# from buildbot.schedulers.forcesched import ForceScheduler
# from buildbot.changes import filter
# config['schedulers'] = []
# config['schedulers'].append(SingleBranchScheduler(
#                             name="all",
#                             change_filter=filter.ChangeFilter(branch='master'),
#                             treeStableTimer=None,
#                             builderNames=["runtests"]))
# config['schedulers'].append(ForceScheduler(
#                             name="force",
#                             builderNames=["runtests"]))
#
# ####### STATUS TARGETS
#
# # 'status' is a list of Status Targets. The results of each build will be
# # pushed to these targets. buildbot/status/*.py has a variety to choose from,
# # including web pages, email senders, and IRC bots.
#
# config['status'] = []
#
# authz_cfg=authz.Authz(
#     # change any of these to True to enable; see the manual for more
#     # options
#     auth=auth.BasicAuth([("pyflakes","pyflakes")]),
#     gracefulShutdown = False,
#     forceBuild = 'auth', # use this to test your slave once it is set up
#     forceAllBuilds = False,
#     pingBuilder = False,
#     stopBuild = False,
#     stopAllBuilds = False,
#     cancelPendingBuild = False,
# )
# config['status'].append(html.WebStatus(http_port=8010, authz=authz_cfg))