
import sys, time
# import signal
from nexusformat.pyro.ssh import NeXpyroSSH

_terminated = False

hostname = "nxrs.msd.anl.gov"
hostname = "130.202.115.40"

# sshService = NeXpyroSSH("wozniak", hostname)
# sshService = NeXpyroSSH("wozniak", hostname, command="echo hi")

# start_server = "/usr/lib/python2.7/site-packages/nexusformat/pyro/start_server.py"
command = "/home/wozniak/proj/nexusformat/src/nexusformat/pyro/start_server.sh"
command = "/home/wozniak/proj/nexusformat/src/nexusformat/pyro/start_server.py"
sshService = NeXpyroSSH("wozniak", hostname, command=command, getURI=True)
uri = sshService.uri
if (uri == "UNSET"):
    print("SSH could not start NeXpyro service!")
    sys.exit(1)
print("uri: " + uri)
tokens = uri.split(":")
port = int(tokens[2])
print(port)
sshTunnel = NeXpyroSSH("wozniak", hostname, localPort=9090, remotePort=port)

time.sleep(200)
