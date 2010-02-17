"""
This is module that integrates pydispatch with the STOMP, XUL Control
and any other protocol to allow event delivery across a network. This 
is used in the web based evasionAtm to route events between the app 
manager, web presence and xul browser. The idea is that code will be 
able to subscribe to real time events any not have to actually be aware
of where these are coming from specifically.

This module requires twisted python (www.twistedmatrix.com),
stomper (http://code.google.com/p/stomper/) and uuid
(http://zesty.ca/python/uuid.html) packages. Twisted can't be
installed via easy_install unfortunately, however stomper and
uuid can.

In addition to the above you also need to download the ActiveMQ
server and install it as a service on you machine. This can be
located here:

 * http://activemq.apache.org/

Oisin Mulvihill
2007-07-27

"""
import logging
import threading

def get_log():
    return logging.getLogger("messenger")


import eventutils
import twistedsetup
import stompprotocol
import xulcontrolprotocol
from events import Event as EVT
from events import LocalEvent as LEVT
from events import ReplyEvent as REVT

from eventutils import send
from eventutils import reply
from eventutils import send_await
from eventutils import wait_for_event
from eventutils import EventTimeout
from eventutils import Catcher



class Runnable(object):
    """Provides a quick way to wait for the stomp connection
    and broker channel subscription.

    You use this class as follows:
    
        stomp_cfg = dict(
            host = ..., 
            :
            etc
        )
            
        class R(director.util.Runnable):
            def ready(self):
                '''Run some server / service until done'''

        r = Runnabled()

        #Set up the messenger stomp protocol and run with callback:
        messenger.stompprotocol.setup(stomp_cfg, connectedOkHandler=r.connectedOk)
        
        # The R:ready() will be running inside its own thread, with 
        # the mainloop reserved for twisted.
        messenger.run(r.run)
    
    """
    def __init__(self):
        self.log = logging.getLogger('director.utils.Runnable')
        self.isReady = threading.Event()
        self.isExit = None
        
    def connectedOk(self):
        """Called when the stop connection is ready"""
        self.isReady.set()
        
    def run(self, isExit):
        """Wait for the ready event the connectOk callback will cause.
        """
        self.isExit = isExit
        get_log().info("run: Waiting for broker connection.")
        self.isReady.wait()
        get_log().info("run: Connection ready.")
        self.ready()

    def ready(self):
        """Override to get called after ready event."""



default_config = {
    #
    # Stomp broker:
    #
    #    host, port:
    #        This is the hostname and port of the system running
    #        the ActiveMQ or other STOMP aware messenger service.
    #
    #    username, password:
    #        These are the auth details required to login in to
    #        the server, if requried.
    #
    #    channel:
    #        Isolate messages from multiple deviceaccesss, using
    #        the same broker, by creating new channels ie evasionoslo,
    #        evasionbmnt, etc
    #
    'stomp' : {
        # defaults:
        'host':'127.0.0.1',
        'port':61613,
        'username':'',
        'password':'',
        'channel':'evasion',
    },
    
    # XUL server socket access:
    #
    'xulcontrol' : {
        'host':'127.0.0.1',
        'port':7055,    
    }
}


from twistedsetup import run
from twistedsetup import quit



