"""
Twisted Network Framework interface functions

Oisin Mulvihill
2007-07-30

"""
import thread
import logging
import threading

from twisted.python import threadable
threadable.init(1)


def get_log():
    return logging.getLogger("messenger.twistedsetup")


import stompprotocol
import xulcontrolprotocol



def quit():
    """Tell the twisted reactor to quit."""
    from twisted.internet import reactor
    try:
        reactor.stop()
    except:
        pass

#
__runner = None

class Run(object):
    """This class is used to run the main application loop
    as a thread inside the twisted loop.

    The contructor takes a function appmain() which
    should accept a single argument. This argument
    is called isExit. This function returns True when
    it is time for the appmain to exit. All other
    times it returns False.
    
    """
    def __init__(self, appmain, kwargs={}):
        self.__foreign_exit_time = threading.Event()
        self.main = appmain
        self.kwargs = kwargs

    def foreignEventLoopStop(self):
        """Called by twisted when its time to stop the thread"""
        self.__foreign_exit_time.set()
    
    def isExit(self):
        """Called by the appmain to determine if its time to exit"""
        return self.__foreign_exit_time.isSet()


    def _exitOneError(self, data):
        """Wrap the func call so that if it raises an exception I
        catch this, then stop twisted reraising the error.
        """
        try:
            self.main(self.isExit, **self.kwargs)
        except:
            # Can't include this globally as it affects the selector install
            quit()
            raise

    def start(self):
        """This is called to start the appmain in its own thread."""
        thread.start_new_thread(self._exitOneError, (0,))
    


# Must come before reactor import:
# Can't include this globally as it affects the selector install
#

def run(appmain=None, **kwargs):
    """Start twisted event loop and the fun should begin...

    appmain:
        This is the programs mainloop that twisted will 
        run inside a thread, to prevent it blocking 
        twisted.

    **kwargs:
        These are any arguments your wished passed to to the
        appmain function at run time.
           
    """
    from twisted.internet import reactor

    if appmain:
        global __runner
        __runner = Run(appmain, kwargs)
        __runner.start()
        reactor.addSystemEventTrigger('after', 'shutdown', __runner.foreignEventLoopStop)
    
    reactor.run(installSignalHandlers=0)
    


   
    

