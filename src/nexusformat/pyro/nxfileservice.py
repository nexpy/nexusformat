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

import threading
import time

from nexusformat.nexus import nxload

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
    root = {}
    path = None

    def initfile(self, name):
        msg("Initializing NXFileService: " + name)
        try:
            msgv("opening", name)
            self.root[name] = nxload(name)
        except Exception as e:
            m = "Caught exception while opening: " + name + "\n" + \
                "Exception msg: " + str(e)
            msg(m)
            return m
        return True

    # We cannot expose __getitem__ via Pyro
    # Cf. pyro-core mailing list, 7/20/2014

    def getitem(self, name, key):
        msgv("getitem", key)
        result = self.root[name][key]
        return result

    # Two-step call sequence
    def getvalue(self, name, path, idx=()):
        msgv("getvalue", idx)
        try:
            msg("get path: " + str(path))
            t = self.root[name][path][idx].nxdata
            msgv('t', t)
            msg("returning t")
        except Exception as e:
            print("EXCEPTION in getvalue(%s): " % idx + str(e))
            t = None
        return t

    def setitem(self, name, key, value):
        """Sets an object value in the NeXus file."""
        msgv("setitem", key)
        self.root[name][key] = value

    # Two-step call sequence
    def setvalue(self, name, path, value, idx=()):
        msgv("setvalue", idx)
        try:
            msg("set path: " + str(path))
            self.root[name][path][idx] = value
        except Exception as e:
            print("EXCEPTION in getvalue(%s): " % idx + str(e))

    def readvalues(self, name, path, attrs):
        with self.root[name].nxfile as f:
            f.nxpath = path
            return f.readvalues(attrs)
            
    def update(self, name, item, path):
        with self.root[name].nxfile as f:
            f.update(item, path)

    def delitem(self, name, path):
        del self.root[name][path]
        
    def tree(self, name):
        return self.root[name]

    def filename(self, name):
        return self.root[name]._filename()

    def setmode(self, name, mode):
        self.root[name]._mode = self.root[name]._file.mode = mode

    def exit(self, code):
        msg("Daemon exiting...")
        thread = threading.Thread(target=shutdown)
        thread.setDaemon(True)
        thread.start()
