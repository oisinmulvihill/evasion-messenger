Evasion Messagener ZMQ
======================

.. contents::

EvasionProject code documentation
---------------------------------

  * http://www.evasionproject.com/apidocs/

EvasionProject Wiki
-------------------

  * http://www.evasionproject.com/


ZMQ Messaging Dev work
----------------------

This branch replaces the twisted+stomper+morbid+pydispatch messaging in favour
of the ZeroMQ Publish-Subscribe (PUB-SUB) implementation. The messenger builds
on the PUB-SUB distributed message dispatch. It provides an ability to register
a callback method to subscribe to a signal string.

Hub
~~~

This is the central process which takes a message and distributes it to all
connected end points.

End Point
~~~~~~~~~

This is a program connecting to a Hub receiving messages and deciding what
action to take based on the evasion frame

Evasion Frames
~~~~~~~~~~~~~~

This is a single ZMQ message which has a particular format. The format is
defined as::

"<message type> <payload>"

Further message types may format the payload. The following message types
exist::

DISPATCH
````````

This frame is used at the Python code level to invoke registered callbacks for
the given signal. The JSON object will be loaded into a python dictionary. It
will contain a source id string and a data dict field. The data dict will be
passed as an argument to any registered callbacks.

For example::

    'DISPATCH <signal string> {"source":"<uuid string>" or "", "data":{...}}'

    'DISPATCH door_open {"source":"", "data":{"a":1}}'
    'DISPATCH stop_sound {"source":"<uuid>", "data":{}}'

DISPATCH_REPLY
``````````````

This is a reply to a received signal. When signal is empty no reply is needed.
If source is not empty the a reply is required. The source from the dispatch
payload is used to return data to a sender waiting for a reply.

For example::

  'DISPATCH_REPLY source_uuid {"a":1}'

HUB_PRESENT
```````````

This frame is sent out periodically by the hub to indicate its presence and will
dispatch messages. The version number present is the version number of the
evasion messenger package.

For example::

'HUB_PRESENT {"version":"X.Y"}'


API
---

All programtic users will subscribe and publish signals via the Register.

messenger.endpoint.Register

    subscribe(signal, function)
        Registers a callback function for a signal. When this signal occurs
        invoke the function with the data dict.

    unsubscribe(signal, function)
        Remove a callback so it is no longer invoked for a signal.

    publish(signal, data)
        Call all subscribers for the signal with the given data.

    start()
        Start receiving messages from the Hub.

    stop()
        Stop receiving messages from the Hub.








