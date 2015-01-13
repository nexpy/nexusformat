
print "HI"

import os, time
from multiprocessing import Process

class SSHProcess:

    def __init__(self, user, host,
                 hours=1, localPort=0, remotePort=0):

        self.user = user
        self.host = host
        self.hours = hours
        self.localPort = localPort
        self.remotePort = remotePort

        self.process = Process(target=self.f, args=())
        self.process.start()

    def account(self):
        return "%s@%s" % (self.user, self.host)

    def f(self):
        self.msg("PID: " + str(os.getpid()));
        self.msg("connecting")
        duration = str(self.hours * 60 * 60)
        command = "sleep " + duration
        argv = ["ssh", self.account()]
        if self.localPort != 0:
            argv.append("-L %i:localhost:%i" % (self.localPort, self.remotePort))
        argv.append(command)
        os.execvp("ssh", argv)
        self.msg("closed")

    def msg(self, m):
        print "SSHProcess:", self.account(), str(m)

    def terminate(self):
        self.msg("killing")
        self.process.terminate()

print "OK"
