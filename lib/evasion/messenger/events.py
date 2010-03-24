"""
This is the top level event that get sent around the system
and out onwards to other remote dispatchers.

Oisin Mulvihill
2007-08-02

"""
import uuid


# What I'm doing here is akin to:
#
#class inch(float):
#...     "Convert from inch to meter"
#...     def __new__(cls, arg=0.0):
#...         return float.__new__(cls, arg*0.0254)
#
# See http://www.python.org/download/releases/2.2.3/descrintro/#__new__
# for more details.
#

class Event(str):
    """This is the base class event that will be send out to
    all dispatchers.

    This allows my event to behave as if they were a string
    signal, but allows me add add custom flags to control
    routing which is transparent to the user.

    PyDispatcher wouldn't work with just straight class
    instances. Its signal matching relies on the instance
    not changing. Which isn't the case in the messenger
    where the instance would change, but the meaning
    wouldn't. The __new__ override allows me to get round
    this problem nicely.

    Note:

        Only events or those derived from this class will
        be sent to remote dispatchers. All other types are
        assumed to be for local delivery and ignored.
    
    """

    def __new__(cls, eid, local_only=False, remote_forwarded=False):
        """Set up the control flags for the new event.

        eid:
            This the string event description for example
            SWIPE_CARD_EVENT. This is what is display when
            you print this class.

        local_only:

            True | False
        
            True: this indicates to the messenger not to
            forward the event onto other remote dispatchers.

        remote_forwarded:

            True | False

            True: this indicates that this event has been
            forwarded from a remote dispatcher. It it used
            not to send this event back out again.

        Once the string has been created then the uid attribute
        is set up. This is the unique identifier for this event
        and is used when replying to this event.
        
        """
        newstr = str.__new__(cls, eid)

        newstr.uid = str(uuid.uuid4())

        # decorate the new string instance with my control flags:
        newstr.eid = eid
        newstr.localOnly = local_only
        newstr.remoteForwarded = remote_forwarded

#        print "returning new instance: ", newstr, newstr.__dict__

        # Return the new instance:
        return newstr

# Shorthand for classes
EVT = Event        
        


class LocalEvent(Event):
    """This is the a local event, it will not be forwarded on to
    other dispatchers.
    
    """
    def __new__(cls, eid, remote_forwarded=False, reply_required=False):
        """This set the local_only flag and it will not be forwarded.

        All other args are passed on to the base.
        
        """
        return Event.__new__(cls, eid, local_only=True, remote_forwarded=remote_forwarded)

# Shorthand for classes
LEVT = LocalEvent        


class ReplyEvent(Event):
    """This is a messenger reply event, used to return
    message content to a waiting subscriber.
    
    """
    def __new__(cls, replyto, local_only=False, remote_forwarded=False):
        """This set the local_only flag and it will not be forwarded.

        replyto:
            This is required and is the uid of the messenger
            event that a reply is for. This is attribute is
            used by the Catcher().sendAndWait(...) when its
            determining who the reply is for.
            
        All other args are passed on to the base.
        
        """
        evt = Event.__new__(cls, "Reply", local_only=local_only, remote_forwarded=remote_forwarded)

        # Set up the reply event only attribute:
        evt.replyto = replyto
        
        return evt

# Shorthand for classes
REVT = ReplyEvent        



