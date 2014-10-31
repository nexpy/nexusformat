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

from nexpyro.nexus import nxload, NXFile

def msg(msg):
    print("pyro server: " + msg)

def msgv(m, v):
    msg(m + ": " + str(v))

def shutdown():
    time.sleep(1)
    daemon.shutdown()


class NXFileService(object):
    name = ""
    nexusFile = None
    root = None
    path = None

    def initfile(self, name):
        msg("Initializing NXFileService: " + name)
        self.filename = name
        try:
            msgv("opening", name)
            self.root = nxload(self.filename)
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
    def getvalue(self, path, idx=()):
        msgv("getvalue", idx)
        try:
            msg("get path: " + str(path))
            t = self.root[path][idx].nxdata
            msgv('t', t)
            msg("returning t")
        except Exception as e:
            print("EXCEPTION in getvalue(%s): " % idx + str(e))
            t = None
        msg("getvalue result: " + str(t))
        return t

    def tree(self):
        print("tree...")
        print "tree root: " , str(self.root)
        return self.root

    def filename(self):
        return self.root._filename()

    def getentries(self):
        print(self.root.getentries())
        return True

    def exit(self, code):
        msg("Daemon exiting...")
        thread = threading.Thread(target=shutdown)
        thread.setDaemon(True)
        thread.start()

