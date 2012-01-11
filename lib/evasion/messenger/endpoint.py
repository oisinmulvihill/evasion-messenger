# -*- coding: utf-8 -*-
"""
"""
import time
import thread
import logging
import threading

import zmq


class Transceiver(object):

    def __init__(self, config={}, message_handler=None):
        """Set up a receiver which connects to the messaging hub.

        :param config: This is a dict in the form::

            config = dict(
                incoming='tcp://*:15566', # default
                outgoing='',
                idle_timeout=1000, # milliseconds:
            )

        """
        self.log = logging.getLogger("evasion.messenger.endpoint.Transceiver")

        self.exitTime = False
        self.context = zmq.Context()

        self.incoming_uri = config.get("incoming", 'tcp://*:15566')
        self.log.info("Recieving on <%s>" % self.incoming_uri)

        self.outgoing_uri = config.get("outgoing", 'tcp://localhost:5567')
        self.log.info("Sending on <%s>" % self.outgoing_uri)

        self.idle_timeout = int(config.get("idle_timeout", 2000))
        self.log.info("Idle Timeout (ms): %d" % self.idle_timeout)

        self.message_handler = message_handler



    def start(self):
        """Set up zmq communication and start receiving messages from the hub.
        """
        self.exitTime = False

        self.incoming = self.context.socket(zmq.SUB)
        self.incoming.setsockopt(zmq.SUBSCRIBE, '')
        self.incoming.connect(self.incoming_uri)

        self.poller = zmq.Poller()
        self.poller.register(self.incoming, zmq.POLLIN)

        def _main(self):
            while not self.exitTime:
                events = self.poller.poll(self.idle_timeout)
                if (events > 0):
                    msg = self.incoming.recv()
                    self.messageIn(msg)

        time.start_new(_main, (0,))


    def stop(self):
        """Stop receiving messages from the hub and clean up.
        """
        self.log.info("stop: shutting down messaging.")
        self.exitTime = True
        self.incoming.close()
        # wait for the poller thread to timeout and exit.
        self.log.info("stop: waiting for receiver shutdown...")
        time.sleep(self.idle_timeout)
        self.log.info("stop: done.")



    def messageOut(self, message):
        """This implements the the DispatcherAdapter dataSend method.

        This is called to send a captured pydispatch signal out for other
        endpoints to receive. The interception of

        """
        outgoing = self.context.socket(zmq.PUSH);
        outgoing.connect(self.outgoing_uri);
        outgoing.send(message)
        outgoing.close()


    def messageIn(self, message):
        """Called on receipt of an evasion frame to determine what to do.
        """



class Register(object):
    """
    """
    def __init__(self, config={}, transceiver=None):
        """
        """
        if not transceiver:
            self.transceiver = Transceiver(config)
        else:
            self.transceiver = transceiver

        self._subscriptions = dict()


    def start(self):
        """
        """

    def stop(self):
        """
        """


    def subscribe(self, signal, callback):
        """Called to subscribe to a string signal.

        :param signal: A signal to subscribe too e.g. tea_time.

        Case is not important an us internally is forced to lower case in all
        operations.

        :param callback: This is a function who takes a two arguments.

        The first argument is a data dict representing any data coming with the
        signal. The second is a source argument. If this is not None then a
        reply is required

        E.g.::

            def my_handler(data, source=None):
                '''Do something no reply'''


            def my_handler(data, source='uuid string'):
                '''Do something and reply with results'''

        """



    def unsubscribe(self, signal, callback):
        """Called to remove a callback for a signal.

        :param signal: The signal used in a call to subscribe.
        :param callback: The function to unsubscribe.

        """


    def local_publish(self, signal, data, source=None):
        """Called on receipt of a message from the messaging queue.
        """


    def publish(self, signal, data, source=None):
        """Called to publish a signal to all subscribers.

        :param signal: The signal used in a call to subscribe.

        :param data: This is a dictionary of data.

        :param source: This is not None

        """




