"""

Pubsub envelope subscriber

Author: Guillaume Aubert (gaubert) <guillaume(dot)aubert(at)gmail(dot)com>

"""
import zmq

def main():
    """ main method """

    # Prepare our context and publisher
    context = zmq.Context(1)
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:5563")
    subscriber.setsockopt(zmq.SUBSCRIBE, "")
    #subscriber.setsockopt(zmq.SUBSCRIBE, "B")

    while True:
        # Read envelope with address
        message = subscriber.recv_multipart()
        if len(message) > 0:
            print("Command <%s>" % (message[0]))
            print("ARGS <%s>" % (message[1:]))
        else:
            print "empty message?!"

    # We never get here but clean up anyhow
    subscriber.close()
    context.term()

if __name__ == "__main__":
    main()

