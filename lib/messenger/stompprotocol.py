"""
This is the twisted specific implementation used to move events
between pydispatcher's to/from remote systems.

Oisin Mulvihill
2007-07-27

"""
import pprint
import pickle
import base64
import logging

import uuid
import twisted
import stomper
from stomper import stompbuffer
from pydispatch import dispatcher
from twisted.protocols import basic
from twisted.internet import threads
from twisted.internet.protocol import Protocol, ReconnectingClientFactory


import messenger


def get_log():
    return logging.getLogger("messenger.stompprotocol")


# A common destination for for messages used across clients:
#
DESTINATION="evasion"



def dump(edict):
    """This takes an event dict, pickles it and base64 encodes it
    ready for transmission.
    """
    evt = pickle.dumps(edict)
    evt = base64.encodestring(evt)
    return evt


def load(message):
    """This reverse the effect of a dump() and returns the orginal dict.
    """
    message = base64.decodestring(message)
    evt = pickle.loads(message)
    return evt

#
# Unit test use only 
#
TESTING_ACTIVE=False


class StompProtocol(Protocol, stomper.Engine):
    """I don't use LineReceiver any more as I'm using the StompBuffer.
    
    StompBuffer can stitch together messages and return a complete
    one when finished. This also means in theory there is no line
    length limit.
    
    """
    def __init__(self, username='', password='', destination=DESTINATION, connectedOkHandler=None):
        stomper.Engine.__init__(self)
        self.destination = destination
        self.username = username
        self.password = password
        self.connectedOkHandler = connectedOkHandler
        self.stompBuffer = stompbuffer.StompBuffer()


    def connectionMade(self):
        """Register with stomp server.
        """
        # Generate the STOMP connect command to get a session.
        cmd = stomper.connect(self.username, self.password)
        self.dataSend(cmd)


    def connected(self, msg):
        """Once I've connected I want to subscribe to message queue.
        """
        from twisted.internet import reactor
        
        stomper.Engine.connected(self, msg)

        get_log().info("Connected: session %s." % msg['headers']['session'])

        # Register the protocol to recieve all events and route them
        # on to the other dispatchers connected to the messenging
        # service.
        dispatcher.connect(
            self.wrapAndSend,
            signal = dispatcher.Any,
            sender = dispatcher.Any,
        )
        get_log().info("Connected: connected wrapAndSend for all signals.")

        # Register for messages from other dispatchers:
        get_log().info("Connected: subscribing to <%s>." % self.destination)

        f = stomper.Frame()
        f.cmd = "SUBSCRIBE"
        f.headers['destination'] = self.destination
        # ActiveMQ specific header: Prevent the messages we send comming back to us.
        f.headers['activemq.noLocal'] = 'true'

        if self.connectedOkHandler:
            # Don't block twisted calling the connected ok handler.
            def _callback():
                try:
                    self.connectedOkHandler()
                except:
                    get_log().exception("connectedOkHandler '%s' blew up when called - " % self.connectedOkHandler)                    
            reactor.callInThread(_callback)
        
        return f.pack()



    def wrapAndSend(self, signal, sender, **kw):
        """Send out an event to other dispatchers.

        signal:
            This is the signal event that we'll forward
            to other pydispatchers.

            Note: only messenger events are forwarded
            to remote dispatchers. Look at the messenger
            E and LE event classes.

        sender:
            This is who sent the event begin sent.

        kw:
            This is a keyword dict of the arguments that
            come with this event.


        Only data types that can be pickled and understood
        by all connected dispatchers should be present in
        the args.

        Note: this function is begin call from a thread so
        I must send data in a thread safe manner. The data
        send method takes care of this.
        
        """
        #get_log().debug("Trying to forward signal: %s" % str((signal, sender)))

        # Ignore events we dispatched or events specifically
        # marked not to forward. We don't forward events as it
        # would lead to a cascade of event sending which is bad.
        # The message server takes care of routing all events.
        # I also don't forward events which aren't from the 
        # messenger.events module.
        #
        if not isinstance(signal, messenger.EVT):
            # This is not a messenger event, don't forward it.
            get_log().debug("Not forwarding (Not a messenger event, just a pydispatch event): %s" % pprint.pformat(signal))
            return

        elif signal.remoteForwarded:
            # This avoid message cascade. We don't forward events
            # as the message broker takes care of this. 
            #get_log().debug("Not forwarding on to remote dispatchers (Remote dispatcher event received): %s" % signal.eid)
            return 

        elif signal.localOnly:
            # Don't send this event remotely, the user doesn't want it to be.
            get_log().debug("Not forwarding (Local Event to this dispatcher): %s" % signal.eid)
            return
            

        f = stomper.Frame()
        f.cmd = "SEND"
        f.headers['destination'] = self.destination
        f.headers['pydispatcher-event'] = 'yes'
        out = dict(signal=signal, sender=sender, data=kw)
        
        try:
            # Events are sent as a dictionary. This has
            # two entries:
            #
            #    event:
            #        This is a string which is the event
            #        interested parties subscribe to.
            #
            #    data:
            #        This is a dictionary which I will 
            #        then pickle ready for transmission.
            #
            f.body = dump(out)
            message = f.pack()
            #get_log().debug("wrapAndSend: forwarding message for signal '%s' - '%s'." % (signal, message))
            
        except:
            get_log().exception("wrapAndSend: Unable to pickle the: %s - " % out)
            
        else:
            # send out the event to remote dispatchers:
            self.dataSend(message)

        
    def ack(self, msg, testingCallback=None, testing=False):
        """Unpickle the received message and then inject it into
        the dispatcher running in this program.

        msg:
            This is a message dict that stomper generates
            after parsing the STOMP message frame.

            The msg['body'] will contain the actual event
            we need to inject into the dispatcher. This 
            signal is from 'messenger.events'. The dict that
            is sent out has the format:

            message = {
                signal : messenger.events event,
                sender : ther sender,
                data : { dict of event args },
            }
            
        testingCallback:
            If this is provided then the actual event delivered
            will be handed to this function, instead of the 
            normal dispatch.            

        """
        message = msg['body']

        def handle(event, testingCallback):
            from twisted.internet import reactor
            
            if testingCallback:
                # Pass over the event for testing.
                testingCallback(event)                
            else:
                # Send as if it was from the dispatcher running in this system.
                def do_send(evt):
                    #get_log().debug("Dispatching remote received event <%s> (%s) locally." % (evt['signal'], evt['signal'].eid))
                    dispatcher.send(
                        signal = evt['signal'],
                        sender = evt['sender'],
                        **evt['data']
                    )                    
                # Don't block the event loop, run it in a thread.              
                if TESTING_ACTIVE:
                    get_log().warn("TESTING: handing to thread for further processing - %s" % event['signal'])
                    thread.start_new_thread(do_send, (event,))
                    
                else:
                    # Doesn't work if I iterate() twisted while testing:
                    reactor.callInThread(do_send, event)

        if message:
            try:
                # Undo transmission protection and recover the event dict:
                event = load(message)
            except:
                get_log().exception("Unable to unpickle the: \"%s\" - " % message)
                
            else:
                # Don't forward the event we've received:
                event['signal'].remoteForwarded = True
                handle(event, testingCallback)

                
        return stomper.NO_REPONSE_NEEDED
        

    def dataSend(self, data):
        """Called to write data out on the transport.
        
        Note: if data is None or empty then nothing will be sent.
        
        """
        from twisted.internet import reactor

        if data:
            # transport.write in this situation as its not thread safe.
            # Therefore I must do this write in the same thread as the
            # reactor is running. To do this I must use reactor.callFromThread
            if not TESTING_ACTIVE:
                def write(data):
                    #get_log().info('dataSend (live mode from reactor thread): data %s' % data)
                    self.transport.write(data)
                    #get_log().info('dataSend data ADDED to buffer')

                #get_log().info('dataSend: calling write() in thread')
                reactor.callFromThread(write, data)
                #get_log().info('dataSend: started write()')
                
            else:
                # Unit test use ONLY, not for production!!
                get_log().warn('dataSend (unit testing mode): data %s' % data)
                self.transport.write(data) # leave it like this for unittests and don't use self.sendLine(data)
                

    def dataReceived(self, data):
        """Use stompbuffer to determine when a complete message has been received. 
        """
        #get_log().info('dataReceived: data chunk %s' % data)
        self.stompBuffer.appendData(data)

        while True:
            msg = self.stompBuffer.getOneMessage()        
            if msg:
                #get_log().info('dataReceived: message %s' % msg)            
                action_id = str(uuid.uuid4())

                # This is run from a thread to perform whatever blocking
                # action. This keeps twisted responding to events.
                def action_stations(msg):
                    # data here should be a frame compatible dict 
                    # as returned by getOneMessage()
                    #get_log().info('dataReceived action_stations: data frame %s' % msg)
                    result = self.react(msg)
                    return result

                # This will send the result in a safe manner once react
                # has determined what is to be returned.
                def ok(resultant_msg):
                    if resultant_msg:
                        #get_log().info('dataReceived ok: sending resultant_msg %s' % resultant_msg)
                        self.dataSend(resultant_msg)
                        #get_log().info('dataReceived ok: DONE')

                def fail(failure, *args):
                    msg = "failure:\n%s, %s\n%s" % (failure.type, failure.getErrorMessage(), failure.getTraceback())
                    get_log().error("action_stations (%s) FAIL: reaction FAIL - %s " % (action_id, msg))

                # Run method in thread and get result as defer.Deferred
                d = threads.deferToThread(action_stations, msg)
                d.addCallback(ok)
                d.addErrback(fail)
            
            else:
                #get_log().info('dataReceived: more data needed, no complete messages yet')
                break
        


class StompClientFactory(ReconnectingClientFactory):
    
    maxDelay = 2

    # Will be set up before the factory is created.
    username, password, destination = '', '', DESTINATION
    
    # If set this will be called when the stomp protcol is
    # connected to the broker and subscribed
    connectedOkHandler = None
    
    def buildProtocol(self, addr):
        return StompProtocol(
            self.username, 
            self.password, 
            self.destination, 
            self.connectedOkHandler,
        )
    
    
    def clientConnectionLost(self, connector, reason):
        """Lost connection
        """
        get_log().info('Lost connection. Reason: %s' % reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
    
    
    def clientConnectionFailed(self, connector, reason):
        """Connection failed
        """
        get_log().info('Connection Failed. Reason: %s' % reason)
        # http://twistedmatrix.com/documents/8.2.0/api/twisted.internet.protocol.ReconnectingClientFactory.html
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)


def setup(config, connectedOkHandler=None):
    """Configure the STOMP Broker connection protocol factory.
    
    config = {
        'host' : '',
        'port' : '',
        'username' : '',
        'password' : '',
        'channel' : 'evasion'
    }

    Isolate messages from multiple deviceaccesss, using
    the same broker, by creating new channels ie evasionoslo,
    evasionbmnt, etc
    
    """
##    print "config: ",config
  
    StompClientFactory.username = config['username']
    StompClientFactory.password = config['password']
    StompClientFactory.connectedOkHandler = connectedOkHandler

    # The destination MUST start with /topic/..
    #
    # For an activemq server /topic/ is used for event
    # publish/subscribe type messages. The /queue/ is more for
    # system like distributed builds where one system gets a 
    # message and then reacts.
    #
    StompClientFactory.destination = '/topic/%s' % (config['channel'])

    # Must come before reactor import:
    import twistedsetup
    import socket

    # Stop twisted import barfing on windows, from stopping 
    # the app from starting. In effect keep importing until
    # it works. It usually will after the 2-3 attempt.
    #    
    while True:
        # Can't include this globally as it affects the selector install
        try:
            from twisted.internet import reactor
        except socket.error, e:
            pass
        else:
            break
    
    reactor.connectTCP(config['host'], config['port'], StompClientFactory())    


