"""
This is a series of handy functions to deal with waiting for
events and the like.

Oisin Mulvihill
2007-07-31

"""
import uuid
import logging
import threading

from pydispatch import dispatcher


import messenger


def get_log():
    return logging.getLogger("messenger.eventutils")


class EventTimeout(Exception):
    """Raise if a wait function times out without receiving an event.
    """


class Catcher(object):
    """This is a helper class used when waiting for events.
    """
    def __init__(self, event, timeout, reply=False):
        """Setup the catcher ready to roll.
        
        event:
            This is the messenger event we are waiting
            to receive, depending on the method call
            used sendAndWait(...) or wait().

        timeout:
            This is the time in seconds to wait for
            events to be received.

        reply: (default: False)

            True | False

            This indicates that a reply is required
            for a sendAndWait. If this is false the

        
        """
        if not isinstance(event, messenger.EVT):
            raise ValueError("Only messenger events can be used with the Catcher class!")

        self.timeout = timeout
        self.evt = event
        self.eventCaught = threading.Event()
        self.event = dict(signal='', sender='', data='')
        self.disconnectFunc = None
        self.reply = reply
       
        if self.reply:
            # Set up the reply sender event handler:
            self.replySender = self.evt.replyto
            self.disconnectFunc = self.replyEventReceiver
        else:
            # Set up the standard for the event (from any sender) straight away:
            self.disconnectFunc = self.eventReceiver

        dispatcher.connect(
            self.disconnectFunc,
            signal=self.evt,
        )


    def replyEventReceiver(self, signal, sender, **data):
        """This is the callback for a REPLY event.
        """
#        print "replyEventReceiver: ", signal, sender, data

        if isinstance(signal, messenger.EVT):
            # Only messenger event can be counted for replies from
            # a send and await.
            #
#            print "signal.replyto:   ", signal.replyto
#            print "self.replySender: ", self.replySender 
#            print
            
            if signal.replyto == self.replySender:
                # Got response:
                self.eventCaught.set()
                self.event['signal'] = signal
                self.event['sender'] = sender
                self.event['data'] = data
                self.eventCaught.set()
            
        
    def eventReceiver(self, signal, sender, **data):
        """This is the callback used as a catch all for the specific event.
        """
#        print "eventReceiver: ", signal, sender, data

        if self.eventCaught.isSet():
            # event caught once already. Ignore the
            # second hit its not for us.
            pass
        else:
            self.eventCaught.set()
            self.event['signal'] = signal
            self.event['sender'] = sender
            self.event['data'] = data


    def sendAndWait(self, event, data):
        """Called to send an event and await its reponse.

        If we haven't received any data after the timeout
        period has elapsed, then the EventTimeout will be
        raised.

        Note:
            This function will only wait for messenger REPLY()
            events. The reason is that only these will contain
            the replyto attribute needed.

        """
        if not self.reply:
            raise ValueError("The reply flag was not set in the constructor before using this method!")
        
        # send the event:
        dispatcher.send(
            signal=event,
            sender=self.replySender,
            data=data,
        )

        # wait for the response:
        return self.wait()


    def wait(self):
        """Called by the user to wait for the event to occur.

        timeout:
            This is a time in seconds.

        If we haven't received any data by the raise
        the timeout exception.

        returned = {
            'event' : '...',
            'sender' : '...',
            'data' : '...'
        }
        
        """
        self.eventCaught.wait(self.timeout)
        
        # Disconnect the event callback.
        try:
            dispatcher.disconnect(self.disconnectFunc)
        except dispatcher.errors.DispatcherKeyError, e:
            pass
        
        if self.eventCaught.isSet():
            # we've got an event, hurragh!
            return self.event


        raise EventTimeout("The event '%s' did not occur within the timeout '%s' (seconds)!" % (self.evt, self.timeout))

    

def send_await(event, data="", timeout=120):
    """Called to send an event and then wait for the response.

    This will use the uid of the sent event as the 'address'
    of who the REPLY is for. If we don't receive this within
    the timeout the EventTimeout will be raised.

    event:
        This is the event string we will register to
        receive.

    data:
        This is the data going out with the event.


    timeout: (120 seconds default)
        This is the time in seconds before the function
        gives up waiting and raises EventTimeout


    returned = {
        'event' : 'REPLY',
        'reponse' : '...'
    }

    NOTE:
    
      response:
        This will contain what ever the reponder returns,
        function response data, etc.
    
    """
    if not isinstance(event, messenger.EVT):
        raise ValueError("Only messenger events can be used with wait_for_event!")

    #get_log().debug("1. send_await: our reply address - %s" % event.uid)
    
    # Set up the reply event connection first so we don't miss it.
    c = Catcher(messenger.REVT(event.uid), timeout, reply=True)

    #get_log().debug("2. Ready for reply. Sending and waiting. ")
    
    evt = c.sendAndWait(event, data)

    #get_log().debug("3. send_await: received reply (%s) for event (%s)." % (evt, event.uid))

    return evt['data']
    
    
    
def wait_for_event(event, timeout=120):
    """Called to wait for a particular event to occur.

    event:
        This is the event string we will register to
        receive.

    timeout: (120 seconds default)
        This is the time in seconds before the function
        gives up waiting and raises EventTimeout


    returned = {
        'event' : '...',
        'sender' : '...',
        'data' : '...'
    }
    
    """
    if not isinstance(event, messenger.EVT):
        raise ValueError("Only messenger events can be used with wait_for_event!")
    
    #get_log().debug("wait_for_event: waiting for (%s)." % (event))
    
    return Catcher(event, timeout).wait()
    
    

def send(event, data):
    """This dispatches a string as a messenger event using the dispatcher.

    This a light weight wrapper around dispatcher.send.

    If the event is already and messenger event
    then this is used unchanged.
    
    """
    if not isinstance(event, messenger.EVT):
        event = messenger.EVT(event)

    dispatcher.send(
        event,
        data=data
    )


def reply(event, data=""):
    """This dispatches a reply string as a messenger event using the dispatcher.

    event:
        This is the messenger event we are replying to. The event
        must be a messenger event or ValueError will be raised.

    data:
        This is any data we might need to send back with
        the reply.

    This a light weight wrapper around dispatcher.send.

    If the event is already and messenger event
    then this is used unchanged.
    
    """
    if not isinstance(event, messenger.EVT):
        raise ValueError("Only messenger events can be replied to!")

    reply_evt = messenger.REVT(event.uid)

    #get_log().debug("reply: sending reply (%s) for (%s)." % (reply_evt, event))

    dispatcher.send(
        reply_evt,
        data=data
    )
    
    #get_log().debug("reply: DONE sending reply (%s) for (%s)." % (reply_evt, event))
