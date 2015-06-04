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
Remote
======

Utilities for parsing remote information such as PyPi and GitHub
releases or tags.
"""

import requests

SESSION = requests.Session()
SESSION.headers.update(
    {"Accept": "application/json", "Content-Type": "application/json"})
PYPI_API = "https://pypi.python.org/pypi/{package}/json"
GITHUB_API = "https://api.github.com/repos/pyfarm/{project}"

def latest_pypi_release(package):
    """
    Returns the version number of the latest release in PyPi.
    """
    url = PYPI_API.format(package=package)
    response = SESSION.get(url)
    response.raise_for_status()
    data = response.json()

    for release, files in data["releases"].items():
        for file_ in files:
            if file_["md5_digest"] == data["urls"][0]["md5_digest"]:
                return release

def remote_tags(project):
    """
    Returns all remote tags for the given project
    """
    url = GITHUB_API.format(project=project) + "/git/refs/tags"
    request = SESSION.get(url)
    request.raise_for_status()
    data = request.json()
    return [entry["ref"].split("/")[-1] for entry in data]

def remote_tag_exists(project, tag):
    return tag in remote_tags(project)
