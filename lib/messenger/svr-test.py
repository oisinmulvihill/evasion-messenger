"""
Server Test used for load testing the messager, pydispatch and the STOMP broker.

To load test start a server and connect it to a broker. The start any amount of
clients setting up there client_id uniquely with typically paysize=10240 and
count=1000. No messages should be lost and no reply or other timeouts should 
occur.


From the root directory it can be run as follows:

PYTHONPATH=.:./director/lib/ python messenger/svr-test.py \
  --logconfig=svrlog.ini --st_host=<stomp broker>


The Server Actions

* This will create counters for a client when it sends a 'setup' message with a
  unique client_id. The server will the send a reply message to the client.

* When a client sends a 'tick' message recover its counter and increment it. The
  server will the send a reply message to the client.
    
* When a client sends a stat message reply with the count. This is typically 
  done only when the client is exiting.


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
parser.add_option("--logconfig", action="store", dest="logconfig", default="svrlog.ini",
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



class Count(object):
    
    def __init__(self):
        self.log = logging.getLogger('server.count')
        self.clients = {}

    def setup(self, signal, sender, data):
        """Add a new client to the dict and set it up waiting for the
        client to set the first count.
        """
        client_id = data['client_id']
        self.clients[client_id] = itertools.count(0)
        messenger.eventutils.reply(signal, 'setup-ok')

        
    def tick(self, signal, sender, data):
        """Increment a clients counter.
        """
        client_id = data['client_id']
        self.log.info("tick: client_id '%s'" % client_id)
        
        # This is just a block of bytes sent to increase the load,
        # its not used for anything
        payload = data['payload']
        self.log.info("tick: received payload bytes '%s'" % len(payload))
        
        if client_id in self.clients:
            current_count = self.clients[client_id].next()            
            self.log.info("tick: incrementing count, current count is '%s'" % current_count)
            rc = dict(result='tick-ok',count=current_count)
            #print("handling client_id:clount %s:%d." % (client_id, current_count))
            messenger.eventutils.reply(signal, rc)
            #print("handle ok - client_id:clount %s:%d." % (client_id, current_count))
            self.log.info("tick: returning '%s'" % rc)
        else:
            self.log.error("Unknown client '%s' attempt to tick a count!" % client_id)


    def stat(self, signal, sender, data):
        """Return the count for a specific client:
        """
        client_id = data['client_id']
        self.log.info("stat: client_id '%s'" % client_id)
        
        if client_id in self.clients:
            current_count = self.clients[client_id].next()            
            self.log.info("stat: returning '%s'" % current_count)
            messenger.eventutils.reply(signal, current_count)            
        else:
            self.log.error("Unknown client '%s' attempt to tick a count!" % client_id)

        

def appmain(isExit):
    """Example of doing a transaction via the terminal:
    """
    log = logging.getLogger()

    log.info("Svr-test Running.")

    import messenger
    from pydispatch import dispatcher

    c = Count()

    # A new client wants to start counting
    dispatcher.connect(
        c.setup,
        signal=messenger.EVT('SETUP_COUNTER'),
    )

    # A client has given us a new count to store
    dispatcher.connect(
        c.tick,
        signal=messenger.EVT('COUNT_TICK'),
    )

    # A client wants to know its count
    dispatcher.connect(
        c.stat,
        signal=messenger.EVT('COUNT_STAT'),
    )
    
    while 1:
        try:
            time.sleep(1)
        except:
            break

    # Finished:
    log.info("Done.")
    messenger.quit()



# Set up the messenger protocols where using:
messenger.stompprotocol.setup(stomp_cfg)

# Run until exit...
messenger.run(appmain)
