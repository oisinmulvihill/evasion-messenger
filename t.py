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

try:
    while True:
        reg.publish('tea_time', dict(a=1))
        time.sleep(5)

except KeyboardInterrupt:
    reg.stop()
