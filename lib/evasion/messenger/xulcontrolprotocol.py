"""
XUL Control Protocol.

This controls the XUL Browser remotely via the control socket,
on which the XUL Browser is waiting to receive commands on. 

Oisin Mulvihill
2007-07-27


"""
import types
import pprint
import urllib
import logging

import simplejson
from pydispatch import dispatcher

from twisted.internet.protocol import Protocol, ReconnectingClientFactory


from evasion import messenger


def get_log():
    return logging.getLogger("evasion.messenger.xulcontrolprotocol")



def dump(control_frame):
    """This takes a control frame dict or other data 
    structure. It converts it to a javascript compatible 
    data type. Finally this is then quoted ready for 
    transmission.
    
    """
    control_frame = simplejson.dumps(control_frame)
    return control_frame


def load(message):
    """This takes a message string returned from the remote
    XUL Browser command. It unquotes it and then attemts to
    load the returned data structure.
    
    """
    message = simplejson.loads(message)
    return message


class XulControlProtocol(Protocol):
    """The XUL Browser control protocol is very simple.

    Once a connection has been established to the server,
    the protocol sets up a pydispatch connection for the
    event 'BROWSER_COMMAND'. 
    
    The data for the event must be in the control frame
    format. This frame is a python dict which will be
    converted into its javascript equivalent object, using
    simplejson.dumps(...).
    
    A command frame has the format:
    
    control frames = {
        'command' : '',
        'args' : ''
    }
    
    command:
        This is string representing the xulcontrol
        command you wish to do.
    
    args:
        This can be any data type that simplejson 
        supports and the remote command can use.

    """

    def connectionMade(self):
        """Ready to roll, connect the BROWSER_COMMAND event.
        
        We should now be able to send commands to the XUL Browser.
        
        """
        get_log().info("Connected to XUL Browser.")
        
        # Connect to the pydispatch for the BROWSER_COMMAND event.
        dispatcher.connect(
            self.wrapAndSend,
            signal = 'BROWSER_COMMAND',
            sender = dispatcher.Any,
        )
        get_log().info("Connected wrapAndSend for BROWSER_COMMAND signal.")


    def wrapAndSend(self, signal, sender, **data):
        """Called to send a control frame to the XUL Browser.

        If you want a reply then the signal must be a
        messenger event wrapping the BROWSER_COMMAND.
        
        """
        get_log().debug("forwarding control_frame: %s" % signal)
        try:
            # dump control frame ready for transmission:
            get_log().info("wrapAndSend: packing ")
            if not isinstance(signal, messenger.EVT):
                # No reply is expected.
                replyto = ''
            else:
                # The uid of the signal is used as the 'address' that
                # a reply goes back to. We'll forward the replyto which
                # the xul browser will return to us later. The method
                # dataReceived then deal with the business of sending a
                # reply.
                replyto = signal.uid

            message = dump(dict(replyto=replyto, data=data['data']))
            
            get_log().info("wrapAndSend: message:   %s" % message)
            
        except:
            get_log().exception("wrapAndSend: failed to wrap control frame - ")
            
        else:
            # Send to the remote side:
            self.dataSend(message)


    def dataSend(self, data):
        """Called to write data out on the transport.
        
        Note: if data is None or empty then nothing will be sent.
        
        """
        if data:
            self.transport.write(data)


    def dataReceived(self, data, testingCallback=None):
        """Data received, react to it and respond if needed.
        """
        # Can't include this globally as it affects the selector install
        from twisted.internet import reactor
        
        get_log().info("dataReceived: received data - %s " % str(data))

        try:
            data = load(data)
            
        except:
            get_log().exception("dataReceived: received data isn't valid json data - ")
            
        else:
            if data['replyto'] == "":
                get_log().debug("dataReceived: no reponse needed for - %s " % data)

            else:
                get_log().debug("dataReceived: sending reply signal to - %s " % data['replyto'])
                
                if testingCallback:
                    # Pass over the event for testing.
                    testingCallback(event)                
                else:
                    # Send the reply which someone may be listeng for somewhere.
                    def do_send():
                        get_log().debug("Dispatching reply event <%s>.")
                        dispatcher.send(
                            signal = messenger.REVT(data['replyto']),
                            data = data['data']
                        )
                    
                    # don't block the event loop, run it in a thread.              
                    reactor.callInThread(do_send)
                
                
        


class XulControlClientFactory(ReconnectingClientFactory):

    maxDelay = 2
    
    def buildProtocol(self, addr):
        return XulControlProtocol()
    
    
    def clientConnectionLost(self, connector, reason):
        """Lost connection: reconnect.
        """
        get_log().info('Lost connection. Reason: %s' % reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
    
    
    def clientConnectionFailed(self, connector, reason):
        """Connection failed? Keep trying until we can get through.
        """
        get_log().info('Connection Failed. Reason: %s' % reason)
        # http://twistedmatrix.com/documents/8.2.0/api/twisted.internet.protocol.ReconnectingClientFactory.html
        self.retry(connector)


def setup(config):
    """Configure the XUL Control connection protocol factory.
    
    config = {
        'host' : '',
        'port' : '',
    }
    
    """
    # Must come before reactor import:
    from evasion.messenger import twistedsetup
    # Can't include this globally as it affects the selector install
    from twisted.internet import reactor
    
    reactor.connectTCP(config['host'], config['port'], XulControlClientFactory())    


