
'''
SESSION.PY

Created on Jan 13, 2015

@author: wozniak

Creates two SSH connections: one to start the service and
one to create an SSH tunnel forwarding the user-provided
local port to the Pyro-selected remote port.  The first
SSH connection allows Pyro to select a free port on the
remote machine, safely reserving it.
'''

from nexusformat.pyro.ssh import NeXPyroSSH

class NeXPyroSession(object):
    '''
    Sets up a NeXPyro session on given host 
    '''

    def __init__(self, user, hostname, localPort):
        self.user = user
        self.hostname = hostname
        self.localPort = localPort
        
    def run(self):
        command = "/home/wozniak/proj/nexusformat/src/nexusformat/pyro/start_server.py"
        self.sshService = NeXPyroSSH(self.user, self.hostname,
                                     command=command, getURI=True)
        uri = self.sshService.uri
        if (uri == "UNSET"):
            print("SSH could not start NeXpyro service!")
            return False
        tokens = uri.split(":")
        port = int(tokens[2])
        self.sshTunnel = NeXPyroSSH(self.user, self.hostname, 
                                    localPort=self.localPort, 
                                    remotePort=port)
        return True
        
    def terminate(self):
        print("session terminating ssh connections...")
        self.sshTunnel.terminate()
        self.sshService.terminate()
