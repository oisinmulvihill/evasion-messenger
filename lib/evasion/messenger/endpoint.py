# -*- coding: utf-8 -*-
"""
"""
import json
import uuid
import thread
import logging
import threading

import zmq
from zmq import ZMQError

from . import frames


class Transceiver(object):

    def __init__(self, config={}, message_handler=None):
        """Set up a receiver which connects to the messaging hub.

        :param config: This is a dict in the form::

            config = dict(
                incoming='tcp://*:15566', # default
                outgoing='tcp://*:15567',
                idle_timeout=1000, # milliseconds:
            )

        """
        self.log = logging.getLogger("evasion.messenger.endpoint.Transceiver")

        self.exitTime = False
        self.context = zmq.Context()

        self.incoming_uri = config.get("incoming", 'tcp://localhost:15566')
        self.log.info("Recieving on <%s>" % self.incoming_uri)

        self.outgoing_uri = config.get("outgoing", 'tcp://localhost:15567')
        self.log.info("Sending on <%s>" % self.outgoing_uri)

        self.idle_timeout = int(config.get("idle_timeout", 2000))
        self.log.info("Idle Timeout (ms): %d" % self.idle_timeout)

        self.message_handler = message_handler


    def main(self):
        """Running the message receiving loop and on idletime check the exit flag.
        """
        self.exitTime = False

        self.incoming = self.context.socket(zmq.SUB)
        self.incoming.setsockopt(zmq.SUBSCRIBE, '')
        self.incoming.connect(self.incoming_uri)

        self.poller = zmq.Poller()
        self.poller.register(self.incoming, zmq.POLLIN)

        while not self.exitTime:
            try:
                events = self.poller.poll(self.idle_timeout)

            except ZMQError as e:
                # 4 = 'Interrupted system call'
                self.log.info("main: sigint or other signal interrupt, exit time <%s>" % e)

            else:
                if (events > 0):
                    msg = self.incoming.recv_multipart()
                    self.message_in(msg)


    def start(self):
        """Set up zmq communication and start receiving messages from the hub.
        """
        def _main(notused):
            self.main()
        thread.start_new(_main, (0,))


    def stop(self):
        """Stop receiving messages from the hub and clean up.
        """
        self.log.info("stop: shutting down messaging.")
        self.exitTime = True
        self.incoming.close()
        self.log.info("stop: done.")


    def message_out(self, message):
        """This sends a message to the messagehub for dispatch to all connected
        endpoints.

        :param message: A tuple of an evasion message.

        """
        outgoing = self.context.socket(zmq.PUSH);
        outgoing.connect(self.outgoing_uri);
        outgoing.send_multipart(message)
        outgoing.close()
        self.log.debug("message_out: sent to hub <%s>" % " ".join(message))


    def message_in(self, message):
        """Called on receipt of an evasion frame to determine what to do.

        The message_handler set in the constructer will be called if one
        was set.

        :param message: A tuple of an evasion message.

        """
        if self.message_handler:
            try:
                self.message_handler(message)
            except:
                self.log.exception("message_in: Error handling received message - ")
        else:
            self.log.debug("message_in: message <%s>" % message)



class Register(object):
    """
    """
    def __init__(self, config={}, transceiver=None):
        """
        """
        self.log = logging.getLogger("evasion.messenger.endpoint.Register")

        self.endpoint_uuid = str(uuid.uuid4())
        if not transceiver:
            self.transceiver = Transceiver(config, self.message_handler)
        else:
            self.transceiver = transceiver

        self._subscriptions = dict()


    def start(self):
        """Call the transceiver's start()."""
        self.transceiver.start()


    def stop(self):
        """Call the transceiver's stop()."""
        self.transceiver.stop()


    def handle_dispath_message(self, endpoint_uuid, signal, data, reply_to):
        """Handle a DISPATCH message.

        :returns: None.

        """
        self.log.debug("handle_dispath_message: %s" % str((endpoint_uuid, signal, data, reply_to)))


    def handle_hub_present_message(self, payload):
        """Handle a HUB_PRESENT message.

        :param payload: This the content of a HUB_PRESENT message from the hub.

        Currently it is a dict in the form: dict(version='X.Y.Z')

        :returns: None.

        """
        #self.log.debug("handle_hub_present_message: %s" % payload)


    def message_handler(self, message):
        """Called to handle a ZMQ Evasion message received.

        :param message: This must be a message in the Evasion frame format.

        For example::

            'DISPATCH some_string {json object}'

            json_object = json.dumps(dict(
                event='some_string',
                data={...}
            ))

        This will result in the publish being call

        """
        fields_present = len(message)

        if fields_present > 0:
            command = message[0]
            if command and isinstance(command, basestring):
                command = command.strip().lower()

            command_args = []
            if fields_present > 1:
                command_args = message[1:]

            if command == "dispatch":
                try:
                    endpoint_uuid, signal, data, reply_to = command_args
                    data = json.loads(data)
                    self.handle_dispath_message(endpoint_uuid, signal, data, reply_to)
                except IndexError:
                    self.log.error("message_handler: invalid amount of fields given to ")

            elif command == "hub_present":
                try:
                    data = json.loads(command_args[0])
                    self.handle_hub_present_message(data)
                except IndexError:
                    self.log.error("message_handler: no version data found in hub present message!")

            else:
                self.log.error("message_handler: unknown command <%s> no action taken." % command)

        else:
            self.log.error("message_handler: invalid message <%s>" % message)


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



    def publish(self, signal, data):
        """Called to publish a signal to all subscribers.

        :param signal: The signal used in a call to subscribe.

        :param data: This is a dictionary of data.

        """
        self.log.debug("publish: sending <%s> to hub with data <%s>"% (signal, data))

        dispatch_message = frames.dispatch_message(
            self.endpoint_uuid,
            signal,
            data,
        )

        self.transceiver.message_out(dispatch_message)



