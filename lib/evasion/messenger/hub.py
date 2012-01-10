# -*- coding: utf-8 -*-
"""
This provides the MessagingHub class which implements a very basic broker which

"""
import json
import thread
import logging
import threading

import zmq

from .frames import HUB_PRESENT


class MessagingHub(object):
    """The messaging hub acts as a message distribution hub between
    all connected end points. The actual business of the distribution
    is handled by zeromq.

    The MessageHub could do something with the messages it receives
    however it currently just blindly sends them for redistribution.

    """
    def __init__(self, config={}):
        """Set up the messaging hub and its internal zeromq sockets.

        :param config: This is a dict in the form::

            config = dict(
                dispatch='tcp://*:15566', # default
                incoming='tcp://*:15567', # default
                idle_timeout=2000, # milliseconds:
            )

        """
        self.log = logging.getLogger("evasion.messenger.MessagingHub")

        self.exitTime = False
        self.wait_for_exit = threading.Event()
        self.context = zmq.Context()

        # This sends messages to all connected client of zeromq:
        self.dispatch = self.context.socket(zmq.PUB)
        dispath_uri = config.get("dispatch", 'tcp://*:15566')
        self.log.info("Dispatching on: %s" % dispath_uri)
        self.dispatch.bind(dispath_uri)

        # This receives a messages from any of the connected clients:
        self.incoming = self.context.socket(zmq.PULL)
        incoming_uri = config.get("incoming", 'tcp://*:15567')
        self.log.info("Incomming on: %s" % incoming_uri)
        self.incoming.bind(incoming_uri)

        idle_timeout = int(config.get("idle_timeout", 2000))
        self.log.info("Idle Timeout (ms): %d" % idle_timeout)
        self.idleTimeout =idle_timeout

        # I use the poller to see if there is an incoming messages,
        # if not I can check if its exit time or do other work.
        self.poller = zmq.Poller()
        self.poller.register(self.incoming, zmq.POLLIN)


    def stop(self, wait=10):
        """Tell main to exit when it next checks the exit flag.

        :param wait: The time in seconds to wait before giving up
        on a clean shutdown.

        """
        self.exitTime = True
        self.wait_for_exit.wait(wait)


    def main(self):
        """Run the message distribution until shutdown is called.
        """
        while not self.exitTime:
            events = self.poller.poll(self.idleTimeout)
            if (events):
                message = self.incoming.recv()
                #self.log.debug("message: <%s>" % message)
                self.dispatch.send(message)

            else:
                #self.log.debug("sending periodic HUB_PRESENT.")
                self.dispatch.send(HUB_PRESENT)

        self.incoming.close()
        self.dispatch.close()
        self.wait_for_exit.set()


    def start(self):
        """Run the messaging main inside a thread.

        Calling stop will cause the thread to exit.

        """
        def _wrap(data=0):
            self.main()
        thread.start_new(_wrap, (0,))

