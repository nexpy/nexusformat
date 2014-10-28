#!/usr/bin/env python 
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
# Copyright (c) 2013-2014, NeXpy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
#-----------------------------------------------------------------------------

"""
Daemon process presenting NeXus file over Pyro
"""

import os
import sys
import threading
import time

import Pyro4

from pyro.nxfileservice import NXFileService


def main():

    # Use automated port number by default
    port = 0
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    whoami = os.environ["USER"]
    service = NXFileService()
    # Make an empty Pyro daemon
    Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
    daemon = Pyro4.Daemon(port=port)
    # Register the object as a Pyro object in the daemon
    # We set the objectId to the user name
    # This means a user can only have 1 daemon object
    uri = daemon.register(service, objectId=whoami)

    # Print the URI so we can use it in the client later
    print("URI: " + str(uri))
    sys.stdout.flush()

    # Start the event loop of the server to wait for calls
    daemon.requestLoop()


if __name__ == '__main__':
    main()
    print "pyro server: Daemon exited."
