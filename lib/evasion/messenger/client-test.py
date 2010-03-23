"""
Client Test used for load testing the messager, pydispatch and the STOMP broker.

To load test start a server and connect it to a broker. The start any amount of
clients setting up there client_id uniquely with typically paysize=10240 and
count=1000. No messages should be lost and no reply or other timeouts should 
occur.


From the root directory it can be run as follows:

PYTHONPATH=.:./director/lib/ python messenger/client-test.py \
  --client_id=<some unique id string>  \
  --logconfig=cli1-log.ini  \
  --paysize=10240  \
  --st_host=<stomp broker>  \
  --count=5000 


Successful run example:

oisin@snorky [evasion-trunk]> PYTHONPATH=.:./director/lib/ python messenger/client-test.py --client_id='mac-cli-1' --logconfig=cli1-log.ini --paysize=10240 --st_host=192.168.0.4 --count=100
Client-test Running.
Sending setup.
Sending counts.
Getting Count Stats.
stat: client_id 'mac-cli-1', count max '100' == server count '100'
Done.
oisin@snorky [evasion-trunk]> 



The Client Actions:

* This will send a 'setup' message and wait for a response.

* Then it will send 'tick' messages to the server containing a payload of bytes and 
  wait for a reply
  
* Once all messages have been sent as fast as it can, a stats message will be sent to 
  the server.
  
* The client will print out a message like stat: 
    client_id 'mac-cli-1', count max '10' == server count '10'

* If the count max equals server count no messages we lost.


Oisin Mulvihill
2009-01-29

"""
import os
import sys
import time
import pprint
import logging
import os.path
import itertools
import logging.config

from pydispatch import dispatcher

from optparse import OptionParser


parser = OptionParser()
parser.add_option("--st_host", action="store", dest="st_host", default=False,
                  help="Stomp broker host to connect to.")
parser.add_option("--st_port", action="store", dest="st_port", default=False,
                  help="Stomp broker host port to connect to.")
parser.add_option("--st_user", action="store", dest="st_user", default=False,
                  help="Stomp broker username to login with (if required).")
parser.add_option("--st_pass", action="store", dest="st_pass", default=False,
                  help="Stomp broker password to login with (if required).")
parser.add_option("--st_channel", action="store", dest="st_channel", default=False,
                  help="Stomp channel on which messages travel, default 'evasion'.")
parser.add_option("--client_id", action="store", dest="client_id", default='not-setup',
                  help="client_id sent in count messages")
parser.add_option("--count", action="store", dest="count", default=10,
                  help="number of messages to send")
parser.add_option("--paysize", action="store", dest="paysize", default=1024 * 10,
                  help="Size of the message payload in bytes")
parser.add_option("--logconfig", action="store", dest="logconfig", default="clilog.ini",
                  help="Logger configuration to use")
(options, args) = parser.parse_args()

import messenger

if os.path.isfile(options.logconfig):
    logging.config.fileConfig(options.logconfig)
else:
    # Set up stdout logging:
    from director import utils
    utils.log_init(logging.INFO)


# Default stomp broker set up:
stomp_cfg = dict(
    host = messenger.default_config['stomp']['host'],
    port = messenger.default_config['stomp']['port'],
    username = messenger.default_config['stomp']['username'],
    password = messenger.default_config['stomp']['password'],
    channel = messenger.default_config['stomp']['channel'],
)

# User stomp overrides:
if options.st_host:
    stomp_cfg['host'] = options.st_host

if options.st_port:
    stomp_cfg['port'] = options.st_port

if options.st_user:
    stomp_cfg['user'] = options.st_user

if options.st_pass:
    stomp_cfg['pass'] = options.st_pass

if options.st_channel:
    stomp_cfg['channel'] = options.st_channel

TIMEOUT = 10


class Count(object):
    
    def __init__(self):
        self.log = logging.getLogger('count')
        self.max = int(options.count)
        self.payload = "A" * int(options.paysize)
        self.client_id = options.client_id

    def setup(self):
        """Set up a counter in the server
        """
        self.log.info("setup: client_id '%s', count max '%s', len(payload) '%s'" % (
            self.client_id,
            self.max,
            len(self.payload),
        ))

        evt = messenger.EVT('SETUP_COUNTER')
        data = dict(
            client_id = self.client_id
        )
                
        self.log.info("setup: sending set up event: '%s'" % evt)
        result = messenger.eventutils.send_await(evt, data, TIMEOUT)
        
        self.log.info("setup result: '%s'" % result)


    def tick(self):
        """Send a count tick and wait for a reply.
        """
        evt = messenger.EVT('COUNT_TICK')
        data = dict(
            client_id = self.client_id,
            payload = self.payload,
        )
        self.log.info("tick: payload bytes '%s' for sending." % len(data['payload']))
                
        self.log.info("tick: sending tick event: '%s'" % evt)
        result = messenger.eventutils.send_await(evt, data, TIMEOUT)
        self.log.info("tick: send result: '%s'" % result)


    def stat(self):
        """Send a count tick and wait for a reply.
        """
        evt = messenger.EVT('COUNT_STAT')
        data = dict(
            client_id = self.client_id,
        )
        self.log.info("stat: sending stat event: '%s'" % evt)
        result = messenger.eventutils.send_await(evt, data, TIMEOUT)

        msg = "stat: client_id '%s', count max '%s' == server count '%s'" % (
            self.client_id,
            self.max,
            result['data'],
        )
        
        self.log.info(msg)
        print(msg)

        

def appmain(isExit):
    """Example of doing a transaction via the terminal:
    """
    log = logging.getLogger()

    # hack: wait for ready...
    time.sleep(10)

    log.info("Client-test Running.")
    print("Client-test Running.")

    log.info("Sending setup.")
    print("Sending setup.")
    c = Count()    
    c.setup()

    log.info("Sending counts.")
    print("Sending counts.")
    i = 0
    while i < c.max:
#        print("Sending %d." % i)
        c.tick()
        i += 1

    # Print out our count and the server counts.
    log.info("Getting Count Stats.")
    print("Getting Count Stats.")
    c.stat()    

    # Finished:
    log.info("Done.")
    print("Done.")
    messenger.quit()
    
    sys.exit(0)
    
    log.info("Exit.")
    print("Exit.")



# Set up the messenger protocols where using:
messenger.stompprotocol.setup(stomp_cfg)

# Run until exit...
messenger.run(appmain)

