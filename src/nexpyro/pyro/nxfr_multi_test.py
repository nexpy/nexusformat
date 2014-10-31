#!/usr/bin/env python

"""
Main client test
"""

import sys

from nxfileremote import nxloadremote

uri = 'PYRO:rosborn@localhost:8802'
name1 = '/home/bessrc/sharedbigdata/data1/osborn-2014-1/bfap00/bfap00_170k.nxs'
name2 = '/Users/rosborn/Desktop/chopper.nxs'

# Convenience: print test number
test_count = 0
def t(): 
    global test_count
    test_count += 1
    print 
    msgv("TEST", test_count)

root1=nxloadremote(name1, uri)
print root1.tree

#root2=nxloadremote(name2, uri)
#print root2.tree
#print root2.entry.data.data[0]
#print root2.entry.data.data[0,5]

print root1.entry.data.v[0,0,0]
print root1.entry.data.v[0,0]


