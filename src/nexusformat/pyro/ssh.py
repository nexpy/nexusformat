
import os
from multiprocessing import Process, Queue
from subprocess import Popen, PIPE, STDOUT

_ssh_process_id = 0

class SSHProcess:

    def __init__(self, user, host,
                 hours=1, localPort=0, remotePort=0,
                 command=None):

        self.user = user
        self.host = host
        self.hours = hours
        self.localPort = localPort
        self.remotePort = remotePort
        self.command = command
        
        self.output = ""
        self.uri = "UNSET"
        
        global _ssh_process_id
        _ssh_process_id += 1
        self.id = _ssh_process_id

        if self.command == None:
            duration = str(self.hours * 60 * 60)
            self.command = "sleep " + duration

        q = Queue() 
        self.process = Process(target=self.f, args=(q,))
        self.process.start()
        result = q.get(block=True, timeout=20)
        self.msg("result: " + result)
        if result.startswith("URI: "):
            self.uri = result.split(" ")[1]

    def account(self):
        return "%s@%s" % (self.user, self.host)

    def f(self, q):
        self.msg("PID: " + str(os.getpid()));
        self.msg("connecting " + self.command)
        argv = ["ssh", self.account(), self.command]
        p = Popen(argv, bufsize=0,
                  stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
        # p.stdin.close()
        while True:
            line = p.stdout.readline()
            self.msg("read: " + line)
            self.output += line
            if line.startswith("URI: "):
                print("found URI %s" % line)
                q.put(line)
                
        exitcode = p.wait()
        result = "exited with code: %i" % exitcode
        self.msg(result)
        q.put(result)

    def msg(self, m):
        print "SSHProcess(%i) %s: %s" % (self.id, self.account(), str(m))

    def terminate(self):
        self.msg("killing")
        self.process.terminate()
