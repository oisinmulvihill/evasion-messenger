#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The time service client shows time updates from the server. This client will
run and stay running regardless of whether a Hub is actually present.

Have a look at time_client2.py to see the use of Hub detection.

"""
import signal
import logging

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

    # Add a handler for the TIME signal and log the UTC time received:
    #
    def time_update(endpoint_uuid, data, reply_to):
        log.info("The time is now '%s'." % data)

    reg.subscribe("TIME", time_update)

    # Set a signal handler to correctly handle Ctrl-C exit time:
    #
    def signal_handler(sig, frame):
        log.warn("signal_handler: signal<%s> caught, stopping." % str(sig))
        reg.stop()

    signal.signal(signal.SIGINT, signal_handler)

    # Run the Register as the main loop which will exit when stop is called:
    #
    reg.main()


if __name__ == "__main__":
    main()