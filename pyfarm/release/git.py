# No shebang line, this module is meant to be imported
#
# Copyright 2015 Oliver Palmer
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Git
===

Module for running common git commands.
"""

import subprocess
from os.path import dirname

from pyfarm.release.utility import check_call

def local_tag_exists(setup_py, tag):
    output = subprocess.check_output(["git", "tag"], cwd=dirname(setup_py))
    return tag in output.splitlines()


def create_tag(setup_py, tag, dry_run=True):
    print("Creating tag %s" % tag)
    check_call(["git", "tag", tag], cwd=dirname(setup_py), dry_run=dry_run)
    check_call(
        ["git", "push", "--tags"], cwd=dirname(setup_py), dry_run=dry_run)

