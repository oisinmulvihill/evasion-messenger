# -*- coding: utf-8 -*-
"""
"""
import unittest
import threading

from evasion.messenger import hub
from evasion.messenger import endpoint


TIMEOUT = 30

class CallBack(object):
    data = None

    def __init__(self):
        self.waiter = threading.Event()

    def wait(self):
        self.waiter.wait(TIMEOUT)
        if not self.data:
            raise ValueError("The callback never called before timeout.")
        # reset for next run:
        self.waiter.clear()

    def __call__(self, data):
        self.data = data
        #print("CallBack: <%s>" % data)
        self.waiter.set()

    def __str__(self):
        return "Test CallBack"



class Messenger(unittest.TestCase):

    def setUp(self):
        """Start the broker running.
        """
        self.broker = hub.MessagingHub()
        self.broker.start()


    def tearDown(self):
        """Stop broker running.
        """
        self.broker.stop()


    def testPublistSubscribe(self):
        """
        """
        reg = endpoint.Register()
        my_cb = CallBack()

        reg.subscribe('tea_time', my_cb)
