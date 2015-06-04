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
Release
=======

Produces a release of the current project.
"""

from __future__ import print_function

from argparse import ArgumentParser
from os.path import isfile, abspath, dirname

from pyfarm.release.parse_setup import get_setup_keyword_value
from pyfarm.release.remote import latest_pypi_release, remote_tag_exists
from pyfarm.release.git import local_tag_exists, create_tag
from pyfarm.release.utility import check_call

try:
    input_ = raw_input
except NameError:
    input_ = input



def release_to_pypi(setup_py, dry_run=True):
    print("Producing PyPi release using %s" % setup_py)
    check_call(
        ["python", "setup.py", "sdist", "upload"],
        dry_run=dry_run,
        cwd=dirname(setup_py)
    )

def release():
    parser = ArgumentParser()
    parser.add_argument(
        "--setup-py", default="setup.py",
        help="The location of the setup.py file (default: %(default)s)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=False,
        help="When provided, do not create a release."
    )
    parser.add_argument(
        "version", nargs="?",
        help="The version to release.  If not provided we will determine the "
             "version from the current value in the setup.py."
    )
    args = parser.parse_args()
    args.setup_py = abspath(args.setup_py)

    if not isfile(args.setup_py):
        parser.error("%s does not exist" % args.setup_py)

    setup_name = get_setup_keyword_value(args.setup_py, "name")
    setup_version = get_setup_keyword_value(args.setup_py, "version")

    print("From %s:" % args.setup_py)
    print("  Package: %s" % setup_name)

    if args.version is None:
        print("  Version: %s" % setup_version)

    answer = input_("Is this information correct? [Y/n] ")

    if answer not in ("Y", "n"):
        parser.error("Expected Y or n")

    if answer == "n":
        parser.error(
            "Cannot continue, invalid parsed information.  Possible bug.")

    release_package = setup_name
    project_name = setup_name.replace(".", "-")
    if args.version is None:
        release_version = setup_version
    else:
        release_version = args.version

    errors = []
    if local_tag_exists(args.setup_py, release_version):
        errors.append("Local tag %s already exists." % release_version)

    if remote_tag_exists(project_name, release_version):
        errors.append("Remote tag %s already exists." % release_version)


    # Make sure we're not attempting to release a version less than the
    # current release on PyPi
    pypi_release = latest_pypi_release(release_package)
    if pypi_release >= release_version:
        errors.append(
            "Release version is {release_version} but latest "
            "PyPi release is {pypi_release}.".format(
                release_version=release_version, pypi_release=pypi_release))

    if errors:
        parser.error(" ".join(errors))

    create_tag(args.setup_py, release_version, dry_run=args.dry_run)
    release_to_pypi(args.setup_py, dry_run=args.dry_run)





