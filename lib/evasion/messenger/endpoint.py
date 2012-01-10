# -*- coding: utf-8 -*-
"""
"""
from pydispatch import dispatcher


class Register(object):
    """
    """
    def __init__(self, config={}):
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


    def publish(self, signal, data, source=None):
        """Called to publish a signal to all subscribers.

        :param signal: The signal used in a call to subscribe.

        :param data: This is a dictionary of data.

        :param source: This is not None

        """