#!/usr/bin/env python
"""
Use nosetests to run the unit tests for this project.

"""
import os
import sys
import logging

import nose

sys.path.extend(["./lib",])

# only run tests from here as the others it finds
# are not unit tests.
env = {}
env['NOSE_WHERE'] = 'lib/messenger/tests,'

result = nose.core.TestProgram(env=env).success
nose.result.end_capture()

