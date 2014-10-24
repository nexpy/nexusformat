#!/usr/bin/env python

# Test pickling NeXus objects 

import nexpy.api.nexus as nx
from nexpy.api.nexus import NXFile, NXroot, NXentry, NXdata, NXfield
from numpy import array

import pickle
import sys

a = NXroot(NXentry(NXdata(NXfield(array((1,2,3,4))))))
f = open('pickle.dump','w')
pickle.dump(a,f)
f.close()
f=open('pickle.dump','r')
b=pickle.load(f)
f.close()
print b.tree
# Expected output: 
# root:NXroot
#   entry:NXentry
#     data:NXdata
#       field = [1 2 3 4]
#         @signal = 1
print b.entry.data.field
# Expected output: 
# NXfield([1 2 3 4])
print b.entry.data.field.dtype
# Expected output: 
# dtype('int64')
