#!/usr/bin/env python

import Pyro4
import sys
import threading
import time

def shutdown():
    time.sleep(1)
    daemon.shutdown()

def message(msg):
    print("pyro server: " + msg)

class TestService1:

    def f1(self, a):
        message("f1(%s)" % str(a))
        return True

    def __getitem__(self, key):
        message("__getitem__")
        return self.getitem(key)
    
    def getitem(self, key):
        message("getitem inputs: " + str(key))
        t = 42
        message("getitem result: " + str(t))
        return t

    def exit(self,code):
        message("Daemon exiting...")
        thread = threading.Thread(target=shutdown)
        thread.setDaemon(True)
        thread.start()
        
service = TestService1()

# Make an empty Pyro daemon
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
daemon = Pyro4.Daemon(host=None, port=8080)
# Register the object as a Pyro object
uri = daemon.register(service, 0)

# Print the URI so we can use it in the client later
print("URI: " + str(uri))
sys.stdout.flush()

# Start the event loop of the server to wait for calls
daemon.requestLoop()
daemon.close()
message("Daemon exited.")
