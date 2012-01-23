import time
import logging

from evasion.messenger import endpoint

log = logging.getLogger()
hdlr = logging.StreamHandler()
fmt = '%(asctime)s %(name)s %(levelname)s %(message)s'
formatter = logging.Formatter(fmt)
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)
log.propagate = False



config = dict()
reg = endpoint.Register(config)
reg.start()


def handler(endpoint, data, reply_to):
	"tea_time handler: endpoint, data, reply_to: ", endpoint, data, reply_to

reg.subscribe('tea_time', handler)

from itertools import count

c = count(0)

payload = "A" * 1024 * 10 * 10

try:
    while True:
        reg.publish('tea_time', dict(tea_time_count=c.next()))
        time.sleep(10)
        #time.sleep(0.01)

except KeyboardInterrupt:
    reg.stop()
