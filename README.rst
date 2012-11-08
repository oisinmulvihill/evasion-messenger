Evasion Messenger
=================

.. contents::

EvasionProject code documentation
---------------------------------

  * http://www.evasionproject.com/apidocs/

EvasionProject Wiki
-------------------

  * http://www.evasionproject.com/


Introduction
------------

The evasion-messenger uses ZeroMQ PUB-SUB pattern to create a distributed
publish-subscribe system. This could be used between processes or across the
network.


Tutorial
--------

Time Service
~~~~~~~~~~~~

In this tutorial we will create two endpoints. The first will be the "server"
who dispatched the current UTC date and time. The second will "client" will
subscribe to time messages and display the current time.

Server
``````

time_server.py:: python

    # need time_server.py code here


Client
``````

time_client.py:: python

    # need time_client.py code here

The code for these are available in the source code examples/timeservice. To
run these examples, start the messagehub and then run the "time_client.py" and
"time_server.py". The order is not important in these examples.

Due to the nature of 0MQ and the PUB-SUB pattern, the "time_client.py" will run
even if no Hub is running. The default hub settings published a HUB_PRESENT
frame periodically.To allow an endpoint to check if anything is
listening, it is possible to checkout an see if

Before we begin, in a new command line terminal run the messagehub. You should
see some output like::

    # Need messagehub default run output


Improved Client
```````````````

time_client2.py:: python

    # need time_client2.py code here


Evasion PUB-SUB Messaging
-------------------------

The original evasion-messenger used a complicated mashup of Twisted, the Stomp
protocol, Morbid and pydispatch. This has now been replaced in favour of
building on the ZeroMQ Publish-Subscribe (PUB-SUB) pattern.

The messenger provides the ability to register a callback function for a signal.
This signal is some user meaningful string. When an endpoint publishes data for
this signal, all callbacks local or remote will be called.

Hub
~~~

This is the central process which takes evasion frames and propagates it to all
connected end points. The Hub only propagates certain frames. Only DISPATCH and
DISPATCH_REPLY reply frames are propagated to endpoints. Other frames are
consumed by the hub.

End Point
~~~~~~~~~

This is a program connecting to a Hub receiving messages and deciding what
action to take based on the evasion frame.

Evasion Frames
~~~~~~~~~~~~~~

The general user does not need to know this. The evasion-messenger takes care
of this. The end-user will deal soley with the endpoint.Register subscribe,
publish or unsubscribe methods.

The Frames are a multipart 0MQ message which when received in Python, becomes a
tuple of strings. The format of the strings in an "Evasion Frame" is defined
as::

(<message type>,(<other>, <contents>, ...))

The <message type> is a string used to give meaning to what the other items
following it will be.


SYNC
````

This frame is used to start a subscribe 0MQ subscribe socket going once it has
started. After one of these has been recieved, you can be sure that other
messages will be handled.

Due to the nature of 0MQ, the Hub or Endpoint does not known when its connected.
Therefore, a SYNC message is sent prior to any message.

The 0MQ guide mentions the need for this in the PUB-SUB pattern, on which the
evasion messenger is built:

  * http://zguide.zeromq.org/page:all#Getting-the-Message-Out

  "There is one more important thing to know about PUB-SUB sockets: you
  do not know precisely when a subscriber starts to get messages. Even
  if you start a subscriber, wait a while, and then start the publisher,
  the subscriber will always miss the first messages that the publisher
  sends. This is because as the subscriber connects to the publisher
  (something that takes a small but non-zero time), the publisher may
  already be sending messages out."

Example Frame::

    ('SYNC', '{"from": "endpoint-<uuid>"}')

    ('SYNC', '{"from": "hub-<uuid>"}')


DISPATCH
````````

This frame is used at the Python code level to invoke registered callbacks for
the given signal. The JSON object will be loaded into a python dictionary. It
will contain a source id string and a data dict field. The data dict will be
passed as an argument to any registered callbacks.

Example Frame::

    ('DISPATCH','3c14d4b7-3b88-4680-96d1-e367f051eef1','tea_time','{"a":1}','0')


DISPATCH_REPLY
``````````````
This is a reply to a received signal. When reply_to is '0' reply is expected. If
reply_to is not '0' it will contain a UUID. This is used to route a reply back
to a waiting process.

Example Frame::

    ('DISPATCH_REPLY', 'proc_uuid', 'reply_to_uuid', '{"a":1}')


HUB_PRESENT
```````````

This frame is sent out periodically by the hub to indicate its presence. The
version number present is the version number of the evasion messenger package.

Example Frame::

    ('HUB_PRESENT', '{"version":"X.Y"}')


Message Flow
````````````

A SYNC frame is sent prior to any message between a Hub and Endpoint. This can
be assumed and will not be mentioned further.

When there is no DISPATCH or DISPATCH_REPLY traffic, the endpoint will receive
HUB_PRESENT messages. These are used to give each endpoint an indication the hub
is present and routing messages.

The Hub will only propagate DISPATCH and DISPATCH_REPLY messages.


"Client" side API
-----------------

All end-users will use the Register class. The Hub will need to be

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


The Hub
-------

If the evasion-messenger is installed with easy_install or the source code is
set up in development mode, a "messagehub" program will be available. This is
run to propagate messages between endpoints.

Configuration
~~~~~~~~~~~~~

The Hub is configured via the command line. It has no configuration file. The
currently available options are::

    $ messagehub --help
    Usage: messagehub [options]

    Options:
      -h, --help           show this help message and exit
      --show-messages      Log all message traffic to DEBUG logging.
      --show-hub-present   Log when HUB_PRESENT is dispatched.
      --wait-for-message-timeout=WAIT_FOR_MESSAGE_TIMEOUT
                           The time (in milliseconds, default: 1000) to wait for
                           messages before timing out and sending a HUB_PRESENT.
      --publish-on=PUBLISH_ON
                           The ZMQ Publish set up, defeault: tcp://*:15566
      --subscribe-on=SUBSCRIBE_ON
                           The ZMQ Subscribe set up, defeault: tcp://*:15567
      --disable-hub-presence
                           Turn off the dispatch of HUB_PRESENCE when idle.




















