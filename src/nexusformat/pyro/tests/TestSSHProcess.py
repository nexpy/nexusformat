
import time
from nexusformat.pyro.ssh import SSHProcess

p = SSHProcess("wozniak", "nxrs.msd.anl.gov", localPort=8080, remotePort=)
time.sleep(10)
p.terminate()
