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

# Until Twisted supports Python 3 we'll stick to Python 2.7.  That said
# we should code as if we're supporting 3.0 now.
import sys
assert sys.version_info[0:2] == (2, 7), "Python 2.7 is required"

from os.path import isfile
from setuptools import setup

if isfile("README.rst"):
    with open("README.rst", "r") as readme:
        long_description = readme.read()
else:
    long_description = ""


setup(
    name="pyfarm.build",
    version="0.1.0",
    packages=[
        "pyfarm",
        "pyfarm.release"
    ],
    namespace_packages=["pyfarm"],
    entry_points={
        "console_scripts": [
            "pyfarm-release = pyfarm.release.entrypoints:release"]},
    install_requires=["requests"],
    url="https://github.com/pyfarm/pyfarm-build",
    license="Apache v2.0",
    author="Oliver Palmer",
    author_email="development@pyfarm.net",
    description="Helper library used for builds including production "
                "of releases.",
    long_description=long_description,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: System :: Distributed Computing"])
