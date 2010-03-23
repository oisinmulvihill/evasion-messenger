#!/usr/bin/env python
# encoding: utf-8
"""
testeventutils.py

Created by Oisin Mulvihill on 2007-07-31.

"""
import time
import thread
import unittest
import threading

from pydispatch import dispatcher

from evasion import messenger


class SignalHelper(object):
    """Testing helper to connect and capture signal and data.
    """
    def __init__(self, signal_event):
        self.data = ""
        self.signal = None
        
        dispatcher.connect(
            self.tc,
            signal=signal_event,
        )

    def tc(self, signal, sender, **data):
        #print "GOT: ", signal
        self.data = data['data']
        self.signal = signal
            


        

class TestEventUtils(unittest.TestCase):
    """Test the event utils helper functions
    """

    def testSend(self):
        """Test the handy send() function.
        """
        testing_event = "Hello there!"
        test_data = "1234"

        sh = SignalHelper(testing_event)
        
        messenger.eventutils.send(testing_event, test_data)
        
        self.assertEquals(sh.data, test_data, "send dispatch failed!")


    def testReply(self):
        """Test the handy reply() function.
        """
        time_out = 1

        event = messenger.EVT("SOME_EVENT")
        self.assertNotEquals(event.uid, '')
        data = dict(data="1234")
        
        def waitAndSignal(data=0):
            # Send the reply after waiting a fixed time for the reciever
            # to be ready. Not a great way of doing this, on a slow machine
            # this might give false positives.
            time.sleep(2)
            messenger.eventutils.reply(event, data)
            
        thread.start_new_thread(waitAndSignal, (data,))

        # Wait for the event to occur:
        timeout = 10
        result = messenger.eventutils.send_await(event, data, timeout)
        self.assertEquals(result['data'], data)

        # Try send_await without using a messenger event and make sure its caught.
        self.assertRaises(ValueError, messenger.eventutils.reply, "Not a Messenger Event", data)


    def testCatcherWithMessengerOnlyEvents(self):
        """Test that only messenger events can be used with the catcher class.
        """
        def bad():
            evt = "Not a Messenger Event"
            messenger.eventutils.Catcher(evt, timeout=1, reply=True)

        self.assertRaises(ValueError, bad)


    def testCatcherWithIncorrectSendAndWaitSetup(self):
        """Test that the reply flag must be set in the catcher construct before sendAndWait is used.
        """
        r = messenger.REVT("1234-456-789-91011")
        c = messenger.eventutils.Catcher(r, timeout=1, reply=False)

        self.assertRaises(ValueError, c.sendAndWait, messenger.EVT("SOME_EVENT"), data=1234)


    def testSendAwait(self):
        """Test the send_await() function sends and gets a response.
        """
        time_out = 1

        event = messenger.EVT("SOME_EVENT")
        self.assertNotEquals(event.uid, '')

        # Set up who the reply is for:
        reply_evt = messenger.REVT(event.uid)
        

        # Check the timeout works when I never receive any reply:
        data = dict(abc=123)
        self.assertRaises(messenger.EventTimeout, messenger.eventutils.send_await, event, data, time_out)


        def waitAndSignal(data=0):
            # Send the reply after waiting a fixed time for the reciever
            # to be ready. Not a great way of doing this, on a slow machine
            # this might give false positives.
            time.sleep(2)
            #print "\nsending reply to: ", testing_uuid, reply_evt
            dispatcher.send(
                signal=messenger.REVT(event.uid),
                data="1234",
            )
        thread.start_new_thread(waitAndSignal, (0,))

        # Wait for the event to occur:
        timeout = 10
        result = messenger.eventutils.send_await(event, data, timeout)
        self.assertEquals(result, dict(data="1234"))

        # Try send_await without using a messenger event and make sure its caught.
        self.assertRaises(ValueError, messenger.eventutils.send_await, "Not a Messenger Event", data, time_out)
        


    def testWaitForEvent(self):
        """Test the wait_for_event() function.
        """
        time_out = 1
        event = messenger.EVT("SOME_EVENT")
        self.assertNotEquals(event.uid, '')
        self.assertRaises(messenger.EventTimeout, messenger.eventutils.wait_for_event, event, time_out)

        def waitAndSignal(data=0):
            time.sleep(2)
            dispatcher.send(
                signal=event,
                data="1234",
            )
        thread.start_new_thread(waitAndSignal, (0,))

        # Wait for the event to occur:
        messenger.eventutils.wait_for_event(event, timeout=10)

    

    
if __name__ == '__main__':
    unittest.main()
