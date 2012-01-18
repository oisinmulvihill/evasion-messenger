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

This is a single message string which has a particular format. The format is
defined as::

"<message type> <process_uuid> <contents>"

The <message type> is a string used to give meaning to what <contents> is for.
The <process_uuid> is the id of the originating endpoint

Further message types may format the payload. The following message types
exist::

DISPATCH
````````

This frame is used at the Python code level to invoke registered callbacks for
the given signal. The JSON object will be loaded into a python dictionary. It
will contain a source id string and a data dict field. The data dict will be
passed as an argument to any registered callbacks.

For example::

    'DISPATCH proc_uuid <signal string> {"reply_to":"<uuid string>" or "", "data":{...}}'

    'DISPATCH 3c14d4b7-3b88-4680-96d1-e367f051eef1 door_open {"reply_to":"", "data":{"a":1}}'
    'DISPATCH 3c14d4b7-3b88-4680-96d1-e367f051eef1 stop_sound {"reply_to":"<uuid>", "data":{}}'

DISPATCH_REPLY
``````````````
This is a reply to a received signal. When reply_to is empty no reply is
expected. If reply_to is not empty then a reply is required. The source from the
DISPATCH payload is used to return data to a sender waiting for a reply.

For example::

  'DISPATCH_REPLY proc_uuid reply_to_uuid {"a":1}'

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








