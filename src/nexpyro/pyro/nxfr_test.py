#!/usr/bin/env python

"""
Main client test
"""

import sys

from nxfileremote import nxloadremote

def msg(m):
    print("pyro test: " + str(m))

def msgv(m, v):
    msg(m + ": " + str(v))
    
if len(sys.argv) == 1:
    name = raw_input("Enter file name: ")
    uri = raw_input("Enter URI: ")
elif len(sys.argv) == 2:
    name = sys.argv.pop()
    uri = raw_input("Enter URI: ")
elif len(sys.argv) == 3:
    uri  = sys.argv.pop()
    name = sys.argv.pop()
else:
    print "usage: client.py <NAME>? <URI>?"
    exit(1)

msg("opening remote file: " + name + " on URI: " + uri)

# Convenience: print test number
test_count = 0
def t(): 
    global test_count
    test_count += 1
    print 
    msgv("TEST", test_count)

nxfr=nxloadremote(name, uri)
print nxfr.tree
while 1:
# print("file: ") #  + str(nxfr._file))
    t()
    f = nxfr["/entry/data/v"]
    msgv("f", f)
    t()
    f = nxfr["/entry/data/v"]
    msgv("f", f)
    t()
    print "Class of f is ", f.__class__
    v = f[0]
    msgv("v", v)
    t()
    v = f[0,0]
    msgv("v", v)
    t()
    v = nxfr["/entry/data/v"][0,0,0]
    msgv("v", v)
    t()
    f1 = nxfr["/entry"]
    msgv("f1", f1)
    f2 = f1["data"]
    msgv("f2", f2)
    break
    
