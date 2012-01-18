# -*- coding: utf-8 -*-
"""
This contains the string templates representing evasion messenger frames.

HUB_PRESENT: 'HUB_PRESENT {"version": "evasion-message package version"}'

DISPATCH: 'DISPATH <signal> <json payload {"source":<uuid>, "data":{...}}>'

DISPATCH_REPLY: 'DISPATCH_REPLY source_uuid {...}'

"""
import json
import pkg_resources

PKG = pkg_resources.get_distribution('evasion-messenger')

__all__ = [
    "hub_present_message", "dispatch_message", "DISPATCH_REPLY",
]


DISPATCH_REPLY = "DISPATCH_REPLY %(source_uuid)s %(payload)s"


def hub_present_message():
    """Return the HUB_PRESENT message which could be sent to the message hub.

    :returns: A string ready for sending.

    For example::

        'HUB_PRESENT {"version":"X.Y.Z"}'

    """
    return "HUB_PRESENT %s" % json.dumps(dict(
        version=PKG.version
    ))


def dispatch_message(proc_uid, signal, data, reply_to=None):
    """Generate a DISPATCH evasion frame which could be sent to the message hub.

    :param signal: This is the string which others will have subscribed to.

    :param data: This is a dictionary of data to send.

    :param reply_to: This is the source which if not None should be replied to.

    :returns: A string ready for sending.

    For example::

        'DISPATCH 3c14d4b7-3b88-4680-96d1-e367f051eef1 door_open {"source":"", "data":{"a":1}}'

    """
    json_data = json.dumps(dict(
        reply_to=reply_to if reply_to else "",
        data=data,
    ))
    return "DISPATCH %(proc_uid)s %(signal)s %(json_data)s" % locals()


