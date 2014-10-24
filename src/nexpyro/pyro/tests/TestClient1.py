#!/usr/bin/env python

"""
Dummy client for prototyping Pyro
"""

import sys
import Pyro4

def message(msg):
    print("pyro client: " + str(msg))

if len(sys.argv) == 1:
    uri = raw_input("Enter URI: ")
elif len(sys.argv) == 2:
    uri = sys.argv[1] 
else:
    print "usage: client.py <URI>"
    exit(1)

# Get a Pyro proxy to the remote object
Pyro4.config.SERIALIZER = "pickle"
proxy = Pyro4.Proxy(uri)
# Also tried this: 
# proxy.__getitem__ = proxy.getitem
b = True

# Use proxy object normally
try:
    print proxy.__dict__
    print dir(proxy)
    # Works:
    b = proxy.f1("hello")
    # Works:
    key1 = "key1"
    value1 = proxy.getitem(key1)
    message("got: %s:%s" % (key1, value1))
    # Works:
    key2 = "key2"
    value2 = proxy.__getitem__(key2)
    message("got: %s:%s" % (key2, value2))
    # Doesn't work:
    key3 = "key3"
    value3 = proxy[key3]
    message("got: %s:%s" % (key3, value3))
except Exception as e:
    print "Caught exception during remote operations!"
    print("Exception message: " + str(e))
    print "Pyro remote traceback:"
    print "".join(Pyro4.util.getPyroTraceback())

message("Shutting down service...")
proxy.exit(0)
if b:
    message("Success.")
else:
    message("Failed!")
    exit(1)
exit(0)
