
"""
LOCAL.PY
Local tests
"""

from nexpy.api.nexus import NXFile
import  nexpy.api.nexus as nx 

import pickle

f = nx.load("f2.nxs")
print(f.tree)

print (pickle.dumps(f))

#f = NXFile("f2.nxs")

##print(f.__dict__)
#d = f["/"]
#print(d)
#t = d.items()
#print(t)
#entry = t[0]
# print(entry)
