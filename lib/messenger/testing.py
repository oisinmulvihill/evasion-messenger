"""
:mod:`testing` -- utilities to aid unit/acceptance/functional testing.
======================================================================

.. module:: messenger.testing
   :platform: Unix, MacOSX, Windows
   :synopsis: utilities to aid unit/acceptance/functional testing
.. moduleauthor:: Oisin Mulvihill <oisin.mulvihill@gmail.com>

.. autoclass:: messenger.testing.Runnable
   :members:
   :undoc-members:
   
.. autoclass:: messenger.testing.MessengerWrapper
   :members:
   :undoc-members:

.. autofunction:: messenger.testing.message_main

"""
import sys
import time
import logging
import traceback
import threading

import stompprotocol
from twistedsetup import run
from twistedsetup import quit


def get_log():
    return logging.getLogger('messenger.testing')


class MessageMainTimeout(Exception):    
    """Raised if a timeout occured waiting to connect
    to the stomp broker.
    """


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
    def __init__(self, timeout=None):
        """
        :param timeout: If this is not None then MessageMainTimeout
        will be raised by run() if it gets no broker connection in
        time.
        
        """
        self.log = logging.getLogger('messenger.testing.Runnable')
        self.isReady = threading.Event()
        self.isExit = None
        self.timeout = timeout
        
    def connectedOk(self):
        """Called when the stop connection is ready"""
        self.isReady.set()
        
    def run(self, isExit):
        """
        Wait for the ready event the connectOk callback will cause.
        
        The wait is not indefinite if timeout is not None. If
        a timeout occurs then MessageMainTimeout will be raised.
        
        """
        self.isExit = isExit

        def a():
            self.log.info("run: Waiting for broker connection (timeout %fs)." % self.timeout)
            self.isReady.wait(self.timeout)
            if self.isReady.isSet():
                self.log.info("run: Connection ready.")
                self.ready()
            else:
                self.log.error("run: connection timed out!")
                def testfail(tc): 
                    raise MessageMainTimeout("Unable to connect to broker as it timed-out")
                self.testfunc = testfail
                self.ready()
                
        def b():
            self.log.info("run: Waiting for broker connection (no timeout).")
            self.isReady.wait()
            self.log.info("run: Connection ready.")
            self.ready()
        
        if self.timeout:
            a()
        else:
            b()

    def ready(self):
        """Override to get called after ready event."""
    
    
class MessengerWrapper(Runnable):
    """This wraps a test function hiding the setup/tear down
    needed to running inside the messaging system. It also
    prevents test from exploding without shutting the messaging
    down properly.
    """
    def __init__(self, testcase, testfunc, timeout=30.0):
        Runnable.__init__(self, timeout)
        self.log = logging.getLogger('messenger.testing.MessengerWrapper')
        self.error = None
        self.testcase = testcase
        self.testfunc = testfunc

    def setUp(self, cfg):
        stompprotocol.setup(cfg, connectedOkHandler=self.connectedOk)
        
    def ready(self):
        """Run the test function now the broker is connected."""
        try:
            # Run the actual tests now that messenger is up and running:
            self.testfunc(self.testcase)
            
        except Exception, e:
            # Capture the exception to raise it in the main thread.
            self.error = sys.exc_info()

        # not py24 friendly :(
        #finally:
        # Exit cleanly no matter what.
        quit()


def message_main(testcase, func, cfg):
    """Runs a test inside the messaging system so signals can 
    be sent and received.
    
    :param testcase: test case object
    
    :param func: function that is your test to be run once
    the messaging system is active and running. The argument
    passed to this function is testcase.
    
    :param cfg: A configuration dict compatible with the
    stomprotocol.setup function.
    
    """
    wrap = MessengerWrapper(testcase, func)
    wrap.setUp(cfg)
    
    # Run twisted until the test finishes:
    run(wrap.run)
        
    if wrap.error:
        # not all error work with raise and a quick fix it to print the error as a string.
        get_log().error("message_main - wrap.error: %s " % str(wrap.error))
        
        # Re-raise the exception from the thread:
        raise wrap.error[0](str(wrap.error[1])+ "".join(traceback.format_tb(wrap.error[2])))
