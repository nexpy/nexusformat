#!/usr/bin/env python

"""
Dummy client for prototyping NexPyro
"""

import sys
import Pyro4

import numpy as np

def message(msg):
    print("pyro client: " + str(msg))

if len(sys.argv) != 3:
    print "usage: client.py <URI> <FILENAME>"
    exit(1)

uri = sys.argv[1]
# raw_input("What is the Pyro uri of the service? ").strip()
name = sys.argv[2]
# raw_input("What is the file name? ").strip()
message("opening remote file: " + name)

# Get a Pyro proxy to the remote object
Pyro4.config.SERIALIZER = "pickle"
proxy = Pyro4.Proxy(uri)
b = True

# Use proxy object normally
try:
    b = proxy.initfile(name)
    # n = proxy.filename()
    t = proxy.tree()
    message("t: " + str(t))
    message("nxname: " + t.nxname)
    # message("tree: " + t.tree)
    # message("entry: " + str(proxy.getitem("/entry/data/v", np.s_[0:4,0:1,0:3])))

    message("data: " + str(t.entry.data.v))
    # message("data: " + str(t.entry.data["signal"]))
    message("value: " + str(t.entry.data.v._value))
    f = proxy.__getitem__("/entry/data/v")
    print "ok 1"
    f = proxy["/entry/data/v"]
    print "ok 2"
    # message("slab: " + str(t.entry.data.v[0,0,0]))
    # print("name="+n)
    pass
except Exception as e:
    print "Caught exception during remote file operations!"
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
