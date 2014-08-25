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

import yaml
from buildbot.buildslave import BuildSlave
from buildbot.buildslave.ec2 import EC2LatentBuildSlave
from buildbot.config import BuilderConfig
from buildbot.status.web import authz, auth
from buildbot.status import html

from master.changesource import GitHubBuildBot

file_cfg = {}

# Load configuration data
with open("private.yml", "r") as private_yaml_file:
    file_cfg.update(yaml.load(private_yaml_file))

with open("config.yml", "r") as public_yaml_file:
    file_cfg.update(yaml.load(public_yaml_file))

buildslave_matrix = {
    "linux": [],
    "mac": [],
    "windows": []
}


# Main configuration read in the .tac file
config = BuildmasterConfig = {
    "title": "PyFarm",
    "titleURL": "https://build.pyfarm.net",
    "buildbotURL": "http://127.0.0.1:8010",
    "db_url": file_cfg["db"],
    "status": [

    ],
    "slaves": [],
    "protocols": {
        "pb": {"port": 9989}
    },
    "change_source": [
        GitHubBuildBot(file_cfg["github_changesource"]["secret"])
    ],
    "builders": [
    ],

}

# Persistent build slave(s)
for name, cfg in file_cfg["slaves"]["persistent"].items():
    file_cfg["buildslave_matrix"][cfg.pop("type")] = name
    config["slaves"].append(
        BuildSlave(name, cfg.pop("passwd"), **cfg))

# AWS build slave(s)
for name, cfg in file_cfg["slaves"]["aws"].items():
    file_cfg["buildslave_matrix"][cfg.pop("type")] = name
    config["slaves"].append(
        EC2LatentBuildSlave(
            name, cfg.pop("passwd"), cfg.pop("instance_type"), **cfg))

# Construct the builder matrix
for project, python_versions in file_cfg["python_versions"].items():
    for python_version in python_versions:
        for platform, buildslaves in buildslave_matrix.items():
            builder = BuilderConfig(
                name="{project}-{platform}-{python_version}".format(**locals()),
                slavenames=buildslaves,
                factory=None  # TODO,
                #mergeRequests=None # TODO?
            )




####### SCHEDULERS

# Configure the Schedulers, which decide how to react to incoming changes.  In this
# case, just kick off a 'runtests' build

from buildbot.schedulers.basic import SingleBranchScheduler
from buildbot.schedulers.forcesched import ForceScheduler
from buildbot.changes import filter
config['schedulers'] = []
config['schedulers'].append(SingleBranchScheduler(
                            name="all",
                            change_filter=filter.ChangeFilter(branch='master'),
                            treeStableTimer=None,
                            builderNames=["runtests"]))
config['schedulers'].append(ForceScheduler(
                            name="force",
                            builderNames=["runtests"]))

####### BUILDERS

# The 'builders' list defines the Builders, which tell Buildbot how to perform a build:
# what steps, and which slaves can execute them.  Note that any particular build will
# only take place on one slave.

from buildbot.process.factory import BuildFactory
from buildbot.steps.source.git import Git
from buildbot.steps.shell import ShellCommand

factory = BuildFactory()
# check out the source
factory.addStep(Git(repourl='git://github.com/buildbot/pyflakes.git', mode='incremental'))
# run the tests (note that this will require that 'trial' is installed)
factory.addStep(ShellCommand(command=["trial", "pyflakes"]))



config['builders'] = []
config['builders'].append(
    BuilderConfig(name="runtests",
      slavenames=["example-slave"],
      factory=factory))

####### STATUS TARGETS

# 'status' is a list of Status Targets. The results of each build will be
# pushed to these targets. buildbot/status/*.py has a variety to choose from,
# including web pages, email senders, and IRC bots.

config['status'] = []

authz_cfg=authz.Authz(
    # change any of these to True to enable; see the manual for more
    # options
    auth=auth.BasicAuth([("pyflakes","pyflakes")]),
    gracefulShutdown = False,
    forceBuild = 'auth', # use this to test your slave once it is set up
    forceAllBuilds = False,
    pingBuilder = False,
    stopBuild = False,
    stopAllBuilds = False,
    cancelPendingBuild = False,
)
config['status'].append(html.WebStatus(http_port=8010, authz=authz_cfg))