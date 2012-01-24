#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Improved time service client which exits if no Hub is running.

"""
import sys
import time
import signal
import logging
import threading

from evasion import common
from evasion.messenger import endpoint


class MyRegister(endpoint.Register):
    """Hook into the hub present to detect when the Hub is running."""

    # timeout in seconds or fractions of:
    NO_HUB_TIMEOUT = 5

    def __init__(self, *args, **kwargs):
        super(MyRegister, self).__init__(*args, **kwargs)
        self.log = logging.getLogger("MyRegister")
        self.is_ready = threading.Event()
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        self.log.warn("signal_handler: signal<%s> caught, stopping." % str(sig))
        self.stop()

    def handle_hub_present_message(self, version):
        if not self.is_ready.is_set():
            # Do only on the first HUB_PRESENT received.
            self.log.info("Received HUB_PRESENT: %s" % version)
            self.is_ready.set()


def main():
    # Set up logging to console to see any useful messages:
    #
    log = common.log.to_console()

    # The register will connect to the default hub settings.
    # See messagehub --help for details.
    #
    reg = MyRegister()
    reg.start()

    log.info("Waiting for a HUB_PRESENT to begin.")
    reg.is_ready.wait(MyRegister.NO_HUB_TIMEOUT)

    if not reg.is_ready.is_set():
        log.error("No HUB is running!")
        reg.stop()
        sys.exit(1)


    log.info("The hub is running subscribing to TIME updates.")
    def time_update(endpoint_uuid, data, reply_to):
        log.info("The time is now '%s'." % data)

    reg.subscribe("TIME", time_update)


    log.info("Running. Press Ctrl-C to exit.")
    while not reg.exit_time:
        # Iterate a GUI event loop / Run a game loop / Do some other work.
        time.sleep(0.1)

    log.info("Finised.")


if __name__ == "__main__":
    main()
