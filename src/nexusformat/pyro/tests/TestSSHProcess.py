
import sys, time
from nexusformat.pyro.ssh import NeXPyroSSH, NeXPyroError

_terminated = False

hostname = "nxrs.msd.anl.gov"
# hostname = "130.202.115.40"

user = "wozniak"

# sshService = NeXpyroSSH("wozniak", hostname)
# sshService = NeXpyroSSH("wozniak", hostname, command="echo hi")

def sleep_safe(seconds):
    try: 
        time.sleep(seconds)
    except KeyboardInterrupt:
        print(" Interrupted!")
        sys.exit(1)

command = "python /home/wozniak/proj/nexusformat/src/nexusformat/pyro/start_server.py"
sshService = NeXPyroSSH(user, hostname, command=command, getURI=True)
try:
    uri = sshService.getURIfromQueue()
except NeXPyroError as e:
    print e
    sshService.terminate()
    sleep_safe(2)
    sys.exit(1)

if (uri == None or uri == "UNSET"):
    print("SSH could not start NeXpyro service!")
    sys.exit(1)
print("uri: " + uri)
tokens = uri.split(":")
port = int(tokens[2])
print("remote port: ", port)
sshTunnel = NeXPyroSSH("wozniak", hostname, localPort=9090, remotePort=port)

sleep_safe(2)
print "done", sshTunnel.done.value
sshTunnel.terminate()
sshService.terminate()

print "sshTunnel  done      ", sshTunnel.done.value
print "sshTunnel  exit code:", sshTunnel.exitcode.value
print "sshService done      ", sshService.done.value
print "sshService exit code:", sshService.exitcode.value
