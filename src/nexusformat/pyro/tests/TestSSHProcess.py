
import time
from nexusformat.pyro.ssh import SSHProcess

hostname = "nxrs.msd.anl.gov"
hostname = "130.202.115.40"

# p = SSHProcess("wozniak", hostname)
# p = SSHProcess("wozniak", hostname, command="echo hi")

# start_server = "/usr/lib/python2.7/site-packages/nexusformat/pyro/start_server.py"
start_server = "/home/wozniak/proj/nexusformat/src/nexusformat/pyro/start_server.py"
command = "python " + start_server
p = SSHProcess("wozniak", hostname, command=command)
time.sleep(2)
print("uri: " + p.uri)
time.sleep(2)
p.terminate()
print("output was: " + p.output)
