#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The time service server which publishes the current UTC time to all endpoints.

"""
import time
import signal
import datetime

from evasion import common
from evasion.messenger import endpoint


def main():
    # Set up logging to console to see any useful messages:
    #
    log = common.log.to_console()

    # The register will connect to the default hub settings.
    # See messagehub --help for details.
    #
    reg = endpoint.Register()

    # Begin the message receiving loop:
    reg.start()

    # Set a signal handler to correctly handle Ctrl-C exit signal:
    def signal_handler(sig, frame):
        reg.stop()
        log.warn("signal_handler: signal<%s> caught, stopping." % str(sig))

    signal.signal(signal.SIGINT, signal_handler)

    # Every five seconds send out the current UTC time as a string:
    while not reg.exit_time:
        now = datetime.datetime.utcnow()
        now = now.isoformat()

        reg.publish('TIME', now)

        time.sleep(5)


if __name__ == "__main__":
    main()
