# -*- coding: utf-8 -*-
"""
This provides the MessagingHub class which implements a very basic broker which

"""
import uuid
import signal
import thread
import logging
import threading
from optparse import OptionParser

import zmq
from zmq import ZMQError

from . import frames


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
                outgoing='tcp://*:15566', # default
                incoming='tcp://*:15567', # default
                idle_timeout=2000, # milliseconds:
                # Set to True to log messages received to DEBUG logging:
                show_messages=False,
                # Set to True to log HUB_PRESNET dispatches:
                show_hub_presence=False,
                # Set to False to not send HUB_PRESENT messages when idle.
                send_hub_present=True,
            )

        """
        self.log = logging.getLogger("evasion.messenger.MessagingHub")

        self.hub_uuid = str(uuid.uuid4())

        self.exit_time = threading.Event()
        self.wait_for_exit = threading.Event()

        # This sends messages to all connected client of zeromq:
        self.outgoing_uri = config.get("outgoing", 'tcp://*:15566')
        self.log.info("Dispatching on: %s" % self.outgoing_uri)

        # This receives a messages from any of the connected clients:
        self.incoming_uri = config.get("incoming", 'tcp://*:15567')
        self.log.info("Incoming on: %s" % self.incoming_uri)

        self.idle_timeout = int(config.get("idle_timeout", 2000))
        self.log.info("Idle Timeout (ms): %d" % self.idle_timeout)

        self.show_messages = bool(config.get("show_messages", False))
        self.show_hub_presence = bool(config.get("show_hub_presence", False))
        self.send_hub_present = bool(config.get("send_hub_present", True))

        self.sync_message = frames.sync_message(
            "hub-%s" % self.hub_uuid
        )


    @classmethod
    def propogate_message(cls, message):
        """Called to determine if a message should propagate to other endpoints.

        This will return False for SYNC messages.

        This will return False for empty messages.

        """
        if not message:
            # Do not propagate empty messages.
            return False

        command = message[0].strip().upper()
        if command in ('HUB_PRESENT','SYNC'):
            return False

        return True


    def stop(self, wait=2):
        """Tell main to exit when it next checks the exit flag.

        :param wait: The time in seconds to wait before giving up
        on a clean shutdown.

        """
        self.exit_time.set()
        self.wait_for_exit.wait(wait)


    def start(self):
        """Run the messaging main inside a thread.

        Calling stop will cause the thread to exit.

        """
        def _wrap(data=0):
            self.main()
        thread.start_new(_wrap, (0,))


    def main(self):
        """Run the message distribution until shutdown is called.

        A SYNC message will be sent before the a message propagated:

          http://zguide.zeromq.org/page:all#Getting-the-Message-Out

          There is one more important thing to know about PUB-SUB sockets: you
          do not know precisely when a subscriber starts to get messages. Even
          if you start a subscriber, wait a while, and then start the publisher,
          the subscriber will always miss the first messages that the publisher
          sends. This is because as the subscriber connects to the publisher
          (something that takes a small but non-zero time), the publisher may
          already be sending messages out.

        """
        self.exit_time.clear()

        context = zmq.Context()

        dispatch = context.socket(zmq.PUB)
        try:
            dispatch.bind(self.outgoing_uri)
        except ZMQError:
            self.log.exception("main: unable to bind to uri <%s> " % (self.outgoing_uri))
            self.exit_time.set()
            return

        incoming = context.socket(zmq.PULL)
        try:
            incoming.bind(self.incoming_uri)
        except ZMQError:
            self.log.exception("main: unable to bind to uri <%s> " % (self.incoming_uri))
            dispatch.close()
            self.exit_time.set()
            return

        def _shutdown():
            self.log.info("main: Waiting for shutdown...")
            dispatch.close()
            incoming.close()
            context.term()
            self.wait_for_exit.set()
            self.log.info("main: Shutdown complete.")

        # I use the poller to see if there is an incoming messages,
        # if not I can check if its exit time or do other work.
        poller = zmq.Poller()
        poller.register(incoming, zmq.POLLIN)

        # Don't check each message whether to log. Do it once with
        # setting a default noop function call if no logging is enabled.
        #
        log_message = lambda msg: None
        if self.show_messages:
            log_message = self.log.debug

        HUB_PRESENT = frames.hub_present_message()
        log_hub_present = lambda: None
        if self.show_hub_presence:
            def log_hub_present():
                self.log.debug("broadcasting HUB_PRESENT to all endpoints.")

        self.log.info("main: Mainloop running.")
        try:
            while not self.exit_time.is_set():
                #self.log.info("main: tick.")
                try:
                    events = poller.poll(self.idle_timeout)
                except ZMQError as e:
                    # 4 = 'Interrupted system call'
                    if e.errno == 4:
                        self.log.info("main: sigint or other signal interrupt, exit time <%s>" % e)
                        break
                    else:
                        self.log.info("main: <%s>" % e)
                        break
                else:
                    if (events):
                        message = incoming.recv_multipart()
                        log_message("main: received<%s>" % message)
                        if self.propogate_message(message):
                            # Sync before begining then send the message:
                            dispatch.send_multipart(self.sync_message)
                            dispatch.send_multipart(message)
                            log_message("main: propagated<%s>" % message)
                    else:
                        if self.send_hub_present:
                            log_hub_present()
                            dispatch.send_multipart(HUB_PRESENT)
        finally:
            _shutdown()
            self.wait_for_exit.set()


def main():
    """The main entry point for the command line messagehub.

    There is no configuration file for messagehub. All options
    are passed via the command line.

    """
    log = logging.getLogger()
    hdlr = logging.StreamHandler()
    fmt = '%(asctime)s %(name)s %(levelname)s %(message)s'
    formatter = logging.Formatter(fmt)
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(logging.DEBUG)
    log.propagate = False

    parser = OptionParser()

    parser.add_option(
        "--show-messages", action="store_true", dest="show_messages",
        default=False,
        help="Log all message traffic to DEBUG logging.",
    )

    parser.add_option(
        "--show-hub-present", action="store_true", dest="show_hub_presence",
        default=False,
        help="Log when HUB_PRESENT is dispatched.",
    )

    DEFAULT_TIMEOUT = 1000
    DEFAULT_PUBLISH_ON = 'tcp://*:15566'
    DEFAULT_SUBSCRIBE_ON = 'tcp://*:15567'

    parser.add_option(
        "--wait-for-message-timeout", action="store", dest="wait_for_message_timeout",
        default=DEFAULT_TIMEOUT,
        help="The time (in milliseconds, default: %d) to wait for messages before timing out and sending a HUB_PRESENT." % DEFAULT_TIMEOUT,
    )

    parser.add_option(
        "--publish-on", action="store", dest="publish_on",
        default=DEFAULT_PUBLISH_ON,
        help="The ZMQ Publish set up, defeault: %s" % DEFAULT_PUBLISH_ON,
    )

    parser.add_option(
        "--subscribe-on", action="store", dest="subscribe_on",
        default=DEFAULT_SUBSCRIBE_ON,
        help="The ZMQ Subscribe set up, defeault: %s" % DEFAULT_SUBSCRIBE_ON,
    )

    parser.add_option(
        "--disable-hub-presence", action="store_true", dest="disable_hub_presence",
        default=False,
        help="Turn off the dispatch of HUB_PRESENCE when idle.",
    )

    (options, args) = parser.parse_args()

    config = dict(
        dispatch=options.publish_on, #'tcp://*:15566', # default
        incoming=options.subscribe_on, #'tcp://*:15567', # default
        idle_timeout=int(options.wait_for_message_timeout),
        show_messages=options.show_messages,
        show_hub_presence=options.show_hub_presence,
        send_hub_present=(not options.disable_hub_presence),
    )

    # Run the hub after setting up handlers for common signals.
    #
    hub = MessagingHub(config)

    def signal_handler(sig, frame):
        log.warn("signal_handler: signal<%s> caught, stopping hub." % str(sig))
        hub.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        hub.main()
    except KeyboardInterrupt:
        hub.stop()



