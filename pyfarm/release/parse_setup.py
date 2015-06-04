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
Parse Setup
===========

Functions for parsing the setup.py file.
"""

import ast


def iter_setup_keywords(setup_py):
    """Generator which yields keywords inside of setup()"""
    with open(setup_py, "rb") as setup:
        parsed = ast.parse(setup.read())

    for node in ast.walk(parsed):
        if isinstance(node, ast.Call) and node.func.id == "setup":
            break
    else:
        raise NameError("Failed to locate setup()")

    for keyword in node.keywords:
        yield keyword

def get_setup_keyword_value(setup_py, keyword):
    """
    Returns the string value of the given keyword inside
    of the setup() function in setup_py.
    """
    for node in iter_setup_keywords(setup_py):
        if node.arg == keyword:
            assert isinstance(node.value, ast.Str)
            return node.value.s