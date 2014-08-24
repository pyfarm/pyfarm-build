import json

import yaml
from buildbot.buildslave import BuildSlave
from buildbot.changes.gitpoller import GitPoller

with open("slaves.yml", "r") as slaves:
  slaves = yaml.load(slaves)


config = BuildmasterConfig = dict(
  slaves=[
    BuildSlave("deb-7-0", slaves["deb-7-0"]["password"]),
    BuildSlave("osx-2012-0", slaves["win-2012-0"]["password"]),
    BuildSlave("win-2012-0", slaves["win-2012-0"]["password"]),
  ]
)

####### BUILDSLAVES


# The 'slaves' list defines the set of recognized buildslaves. Each element is
# a BuildSlave object, specifying a unique slave name and password.  The same
# slave name and password must be configured on the slave.

config['slaves'] = [BuildSlave("example-slave", "pass")]

# 'protocols' contains information about protocols which master will use for
# communicating with slaves.
# You must define at least 'port' option that slaves could connect to your master
# with this protocol.
# 'port' must match the value configured into the buildslaves (with their
# --master option)
config['protocols'] = {'pb': {'port': 9989}}

####### CHANGESOURCES

# the 'change_source' setting tells the buildmaster how it should find out
# about source code changes.  Here we point to the buildbot clone of pyflakes.


config['change_source'] = []
config['change_source'].append(GitPoller(
        'git://github.com/buildbot/pyflakes.git',
        workdir='gitpoller-workdir', branch='master',
        pollinterval=300))

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

from buildbot.config import BuilderConfig

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

from buildbot.status import html
from buildbot.status.web import authz, auth

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

####### PROJECT IDENTITY

# the 'title' string will appear at the top of this buildbot
# installation's html.WebStatus home page (linked to the
# 'titleURL') and is embedded in the title of the waterfall HTML page.

config['title'] = "Pyflakes"
config['titleURL'] = "https://launchpad.net/pyflakes"

# the 'buildbotURL' string should point to the location where the buildbot's
# internal web server (usually the html.WebStatus page) is visible. This
# typically uses the port number set in the Waterfall 'status' entry, but
# with an externally-visible host name which the buildbot cannot figure out
# without some help.

config['buildbotURL'] = "http://localhost:8010/"

####### DB URL

config['db'] = {
    # This specifies what database buildbot uses to store its state.  You can leave
    # this at its default for all but the largest installations.
    'db_url' : "sqlite:///state.sqlite",
}
