# -*- coding: utf-8 -*-
"""
This provides HubHelper which requires evasion-messenger
to be installed.

"""
import logging


class TestModuleHelper(object):
    """This provides a why to setup and tear down a hub for testing with nose.

    This will create a hub running on a random free port it will
    choose for subscription and publication

    """
    def __init__(self):
        """Call setup_module / teardown_module inside you module
        which nosetests will pickup.

        """
        m = "evasion.common.testing.withhub.TestModuleHelper"
        self.log = logging.getLogger(m)
        self.config = {}
        self.broker = None


    def setup_module(self, module=None):
        """Set up a test hub on a random free incoming/outgoing port.

        This will attempt to import evasion.messenger modules.

        This will populate self.config with the current configuration.

        For example::

            self.config = dict(
                endpoint=dict(
                    incoming='tcp://localhost:%d'%port1,
                    outgoing='tcp://localhost:%d'%port2,
                ),
                hub=dict(
                    outgoing='tcp://*:%d'%port1,
                    incoming='tcp://*:%d'%port2,
                    # Set to True to log messages received to DEBUG logging:
                    show_messages=True,
                    # Set to True to log HUB_PRESNET dispatches:
                    show_hub_presence=False,
                    # Disable HUB_PRESENT in testing
                    send_hub_present=False,
                )
            )

        """
        self.log.info("setup_module: for <%s>" % module)

        from evasion.common import net
        from evasion.messenger import hub

        port1 = net.get_free_port()
        port2 = net.get_free_port(exclude_ports=[port1])

        self.config = dict(
            endpoint=dict(
                incoming='tcp://localhost:%d'%port1,
                outgoing='tcp://localhost:%d'%port2,
            ),
            hub=dict(
                outgoing='tcp://*:%d'%port1,
                incoming='tcp://*:%d'%port2,
                # Set to True to log messages received to DEBUG logging:
                show_messages=True,
                # Set to True to log HUB_PRESNET dispatches:
                show_hub_presence=False,
                # Disable HUB_PRESENT in testing
                send_hub_present=False,
            )
        )
        self.log.debug("setup_module: generated configuration %s" % self.config)

        self.broker = hub.MessagingHub(self.config['hub'])
        self.broker.start()

        self.log.info("setup_module: the hub has been started.")


    def teardown_module(self, module=None):
        """Stop the running test hub.
        """
        self.log.info("teardown_module: for <%s>" % module)
        if self.broker:
            self.broker.stop()
            self.log.info("teardown_module: the hub has been stopped.")
