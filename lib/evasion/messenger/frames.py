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
    "HUB_PRESENT", "DISPATCH", "DISPATCH_REPLY",
]

HUB_PRESENT = "HUB_PRESENT %s" % json.dumps(dict(
    version=PKG.version
))

DISPATCH = "DISPATCH %(signal)s %(payload)s"

DISPATCH_REPLY = "DISPATCH_REPLY %(source_uuid)s %(payload)s"

