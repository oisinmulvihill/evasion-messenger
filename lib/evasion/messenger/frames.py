# -*- coding: utf-8 -*-
"""
This contains the string templates representing evasion messenger frames.

"""
import json
import pkg_resources

PKG = pkg_resources.get_distribution('evasion-messenger')

__all__ = [
    "hub_present_message", "dispatch_message", "dispatch_reply_message",
]


def hub_present_message():
    """Return the HUB_PRESENT message which could be sent to the message hub.

    :returns: A multi-part HUB_PRESENT message.

    For example::

        ('HUB_PRESENT', '{"version":"X.Y.Z"}')

    """
    return ("HUB_PRESENT", json.dumps(dict(version=PKG.version)))


def dispatch_message(endpoint_id, signal, data, reply_to=None):
    """Generate a DISPATCH evasion frame which could be sent to the message hub.

    :param endpoint_id: The UUID of the dispatching endpoint.

    :param signal: This is the string which others will have subscribed to.

    :param data: The json encoding compative dict of data.

    :param reply_to: This is the source which if not None should be replied to.

    :returns: A multi-part HUB_PRESENT message.

    For example::

        (
            # The command:
            'DISPATCH',

            # The source endpoint UID of the dispatching end point.
            '3c14d4b7-3b88-4680-96d1-e367f051eef1',

            # Signal to publish in endpoints.
            'door_open',

            # The data to publish with the signal:
            {"data":{"a":1}}',

            # The UUID of the reply to or 'no_reponse'.
            '0' or '<uuid of a reply>', # Reply to addres.
        )

    """
    json_data = json.dumps(data)

    return (
        "DISPATCH",
        str(endpoint_id),
        str(signal),
        json_data,
        str(reply_to) if reply_to else '0'
    )


def dispatch_reply_message(reply_to, data):
    """Generate a DISPATCH_REPLY for

    :param reply_to: The UUID which is waiting for the reply data.

    :param data: The json encoding compative dict of data.

    """
    json_data = json.dumps(data)

    return (
        "DISPATCH_REPLY",
        str(reply_to),
        json_data,
    )

