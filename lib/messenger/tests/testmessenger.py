#!/usr/bin/env python
# encoding: utf-8
"""
testmessenger.py

Created by Oisin Mulvihill on 2007-07-30.

"""
import pprint
import unittest

import stomper
from pydispatch import dispatcher

import messenger

# Short circuit the twisted code for testing. NOT for production use!!
messenger.stompprotocol.TESTING_ACTIVE = True

        
class FakeTransport(object):
    def __init__(self):
        self.data = None
    def write(self, cmd):
        self.data = cmd


class TestMessenger(unittest.TestCase):
    """Exercise the stomp and xulcontrol protocols code along with any related functionality.
    """


    def testStompProtocol(self):
        """Test as much of the StompProtocol class as I can.
        """
        username, password = 'bob', '1234'
        protocol = messenger.stompprotocol.StompProtocol(username, password)
        protocol.transport = FakeTransport()

        # Check connection made
        protocol.connectionMade()
        
        correct = stomper.connect(username, password)
        self.assertEquals(protocol.transport.data, correct)
        protocol.transport.data = None

        msg = stomper.unpack_frame("""CONNECTED
session:ID:snorky.local-49191-1185461799654-3:18

\x00
""")
        
        # Check the connected handler and the signal connect
        # it should now have set up.
        result = protocol.connected(msg)

        # This is the subscribe command it'll setup now:
        f = stomper.Frame()
        f.cmd = "SUBSCRIBE"
        f.headers['destination'] = messenger.stompprotocol.DESTINATION
        # ActiveMQ specific header: Prevent the messages we send comming back to us.
        f.headers['activemq.noLocal'] = 'true'

        self.assertEquals(result, f.pack())


        # Test the event ignoring for events that are not to be forwarded.
        #
        # Any events that are not a messenger event are ignored.
        #
        protocol.transport.data = None

        dispatcher.send(
            signal='SOME_EVENT',
            data=[1,2,3,4,5,6,7,8,9,0]            
        )

        self.assertEquals(protocol.transport.data, None)

        class Event(object):
            """test event.
            """
        evt = Event()

        dispatcher.send(
            signal=evt,
            data=[1,2,3,4,5,6,7,8,9,0]            
        )

        self.assertEquals(protocol.transport.data, None)


        # Test the messenger event capture ignoring and forwarding:
        #
        protocol.transport.data = None
        
        dispatcher.send(
            signal=messenger.EVT('SOME_EVENT'),
            sender="testsnd",
            data=[1,2,3,4,5,6,7,8,9,0]            
        )

        f = stomper.Frame()
        f.cmd = "SEND"
        f.headers['pydispatcher-event'] = 'yes'
        f.headers['destination'] = messenger.stompprotocol.DESTINATION
        correct_out = dict(
            signal=messenger.EVT('SOME_EVENT'),
            sender="testsnd",
            data={'data':[1,2,3,4,5,6,7,8,9,0]})
            
        f.body = messenger.stompprotocol.dump(correct_out)
        correct_message = f.pack()

#        print "Correct"
#        pprint.pprint(correct_message)
#        print "Correct"
#        pprint.pprint(correct_out)
#        print
        
#        print "Result"
#        pprint.pprint(protocol.transport.data)
#        print "Result"
        f = stomper.unpack_frame(protocol.transport.data)
        result = messenger.stompprotocol.load(f['body'])
#        pprint.pprint(result)
#        print
        
        self.assertEquals(result, correct_out)
        
        protocol.transport.data = None


        # local only
        dispatcher.send(
            signal=messenger.EVT('SOME_EVENT', local_only=True),
            data=[1,2,3,4,5,6,7,8,9,0]            
        )

        self.assertEquals(protocol.transport.data, None)

        # local only
        dispatcher.send(
            signal=messenger.LEVT('SOME_EVENT'),
            sender=dispatcher._Anonymous,
            data=[1,2,3,4,5,6,7,8,9,0]            
        )

        self.assertEquals(protocol.transport.data, None)
        
        
        # Test the event receive end of the protocol:
        msg = stomper.unpack_frame(correct_message)
        
        class CB(object):
            returned = None
            def callback(self, evt):
                self.returned = evt
                
        cb = CB()
        protocol.ack(msg, cb.callback)

##         print "Correct"
##         pprint.pprint(correct_out)
##         print

##         print "result"
##         pprint.pprint(cb.returned)
##         print
        
        self.assertEquals(cb.returned['data'], correct_out['data'])
        self.assertEquals(cb.returned['sender'], correct_out['sender'])
        self.assertEquals(cb.returned['signal'].eid, correct_out['signal'].eid)
        self.assertEquals(cb.returned['signal'].remoteForwarded, True)



    def testXulControlProtocol(self):
        """Test as much of the StompProtocol class as I can.
        """
        protocol = messenger.xulcontrolprotocol.XulControlProtocol()    
        protocol.transport = FakeTransport()
        protocol.transport.data = None
        
        # Check connection made and the signal connect
        # it should now have set up.
        protocol.connectionMade()

        control_frame = {
            'command' : 'set_uri',
            'args' : {'uri':'http://www.google.com'}
        }

        out = dict(replyto='', data=control_frame)

        dispatcher.send(
            signal='BROWSER_COMMAND',
            data=control_frame,          
        )

        correct_message = messenger.xulcontrolprotocol.dump(out)
        
        self.assertEquals(protocol.transport.data, correct_message)
        

        # Check replyto addition:
        sender = ""
        out = dict(replyto=sender, data=control_frame)

        dispatcher.send(
            signal='BROWSER_COMMAND',
            sender=sender,
            data=control_frame,          
        )

        correct_message = messenger.xulcontrolprotocol.dump(out)
#
#        print "Correct"
#        pprint.pprint(correct_message)
#        print
#
#        print "result"
#        pprint.pprint(protocol.transport.data)
#        print
        
        self.assertEquals(protocol.transport.data, correct_message)


        # Check it ignores other types of senders:
        sender = "SENDERxyz"
        out = dict(replyto='', data=control_frame)

        dispatcher.send(
            signal='BROWSER_COMMAND',
            sender=sender,
            data=control_frame,          
        )

        correct_message = messenger.xulcontrolprotocol.dump(out)
        
        self.assertEquals(protocol.transport.data, correct_message)

        sender = "SENDERxyz"
        out = dict(replyto='', data=control_frame)

        dispatcher.send(
            signal='BROWSER_COMMAND',
            sender=sender,
            data=control_frame,          
        )

        correct_message = messenger.xulcontrolprotocol.dump(out)
        
        self.assertEquals(protocol.transport.data, correct_message)


        # Check the reply handling:
        returned = {
            'result' : 'ok',
            'replyto' : '',
            'data' : '',
        }
        msg = messenger.xulcontrolprotocol.dump(returned)

        def callback(evt):
            self.assertEquals(evt, returned)

        protocol.dataReceived(msg, testingCallback=callback)



    def testXulControlDumpAndLoad(self):
        """Test that xul control dump and load is functional.
        """
        original = {
            'command' : 'redirect',
            'data' : [1,2,3]
        }
        
        part1 = messenger.xulcontrolprotocol.dump(original)
        
        new = messenger.xulcontrolprotocol.load(part1)
        
        self.assertEquals(original, new, "Dump and load failed!")
        

    def testStompDumpAndLoad(self):
        """Test that stomp protocol dump and load is functional.
        """
        original = {
            'event' : 'SWIPE_CARD_DATA',
            'data' : "1234567890"
        }
        
        part1 = messenger.stompprotocol.dump(original)
        
        new = messenger.stompprotocol.load(part1)
        
        self.assertEquals(original, new, "Dump and load failed!")
        
        

    
if __name__ == '__main__':
    unittest.main()
