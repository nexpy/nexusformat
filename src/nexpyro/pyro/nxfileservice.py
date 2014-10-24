#!/usr/bin/env python

"""
Daemon process presenting NeXus file over Pyro
"""

import os
import sys
import threading
import time

import Pyro4

import nexpyro.nexus as nx
from nexpyro.nexus import NXFile

def msg(msg):
    print("pyro server: " + msg)

def msgv(m, v):
    msg(m + ": " + str(v))

def shutdown():
    time.sleep(1)
    daemon.shutdown()

# Use automated port number by default
port = 0
if len(sys.argv) > 1:
    port = int(sys.argv[1])

whoami = os.environ["USER"]

class NXFileService:
    name = ""
    nexusFile = None
    root = None
    path = None

    def initfile(self, name):
        msg("Initializing NXFileService: " + name)
        self.name = name
        try:
            msgv("opening", name)
            self.nexusFile = NXFile(name, 'r')
            self.root = nx.load(self.name) # , close=False
            self.root._proxy = True
            nx.setserver(True)
        except Exception as e:
            m = "Caught exception while opening: " + name + "\n" + \
                "Exception msg: " + str(e)
            msg(m)
            return m
        return True

    # We cannot expose __getitem__ via Pyro
    # Cf. pyro-core mailing list, 7/20/2014

    def getitem(self, key):
        msgv("getitem", key)
        result = self.root[key]
        msgv("result", result)
        return result

    # Two-step call sequence
    def getdata(self, key):
        msgv("getdata", key)
        try:
            msg("get path: " + str(self.path))
            if self.path == None:
                self.path = key
                msg("ok")
                t = self.root[self.path]
                msg("returning t")
            else:
                g = self.root[self.path]
                print("g: " + str(g))
                t = g[key]
                self.path = None
            msg("set path: " + str(self.path))
        except Exception as e:
            print("EXCEPTION in getitem(): " + str(e))
            t = None
        msg("getitem result: " + str(t))
        return t

    def tree(self):
        print("tree...")
        print "tree root: " , str(self.root)
        return self.root

    def filename(self):
        return self.nexusFile.filename()

    def getentries(self):
        print(self.nexusFile.getentries())
        return True

    def exit(self,code):
        msg("Daemon exiting...")
        thread = threading.Thread(target=shutdown)
        thread.setDaemon(True)
        thread.start()

nxfileservice = NXFileService()

# Make an empty Pyro daemon
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
daemon = Pyro4.Daemon(port=port)
# Register the object as a Pyro object in the daemon
# We set the objectId to the user name
# This means a user can only have 1 daemon object
uri = daemon.register(nxfileservice, objectId=whoami)

# Print the URI so we can use it in the client later
print("URI: " + str(uri))
sys.stdout.flush()

# Start the event loop of the server to wait for calls
daemon.requestLoop()
msg("Daemon exited.")
