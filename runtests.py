#!/usr/bin/env python
"""
Use nosetests to run the unit tests for this project.

"""
import sys
import logging

import nose

log = logging.getLogger('evasion')
hdlr = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)
log.propagate = False

sys.path.extend(["./lib",])

# only run tests from here as the others it finds
# are not unit tests.
env = {}
env['NOSE_WHERE'] = 'lib/evasion/messenger/tests,'

result = nose.core.TestProgram(env=env).success
nose.result.end_capture()

