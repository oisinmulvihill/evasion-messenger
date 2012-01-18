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


config = dict(
)

trans = endpoint.Transceiver(config)
trans.start()

try:
    while True:
        msg = "HELLO THERE"
        trans.message_out(msg)
        time.sleep(5)

except KeyboardInterrupt:
    trans.stop()
