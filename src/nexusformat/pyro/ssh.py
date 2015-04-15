
'''
SSH.PY

Created on Jan 12, 2015

@author: wozniak

Creates an SSH connection for use by NeXPyroSession.
Features:
1) automated termination
2) local port forwarding
3) a mechanism to get the URI from a NeXPyro service
'''

import os, sys, time
import select
from select import POLLIN
from multiprocessing import Process, Queue, Value
from ctypes import c_bool, c_int
from Queue import Empty
from subprocess import Popen, PIPE, STDOUT

_ssh_process_id = 0

class NeXPyroSSH:

    '''
    Automated termination: good for use with port forwarding.
       Set hours and leave command unset
    Local port forwarding: just set localPort and remotePort
    Retrieve Pyro URI: set getURI=True, then call
       getURIfromQueue(), the result is cached in the
       NeXPyroSSH.uri variable
    '''
    def __init__(self, user, host,
                 hours=1, localPort=0, remotePort=0,
                 command=None, getURI=False):

        self.user = user
        self.host = host
        self.hours = hours
        self.localPort = localPort
        self.remotePort = remotePort
        self.command = command
        self.getURI = getURI

        self.output = ""
        self.uri = "UNSET"

        global _ssh_process_id
        _ssh_process_id += 1
        self.id = _ssh_process_id

        if self.command == None:
            duration = str(self.hours * 60 * 60)
            self.command = "sleep " + duration

        # Sends messages down to subprocess
        self.queueDown = Queue()
        # Sends messages up from subprocess
        self.queueUp = Queue()
        self.done = Value(c_bool, False, lock=True)
        self.exitcode = Value(c_int, 0, lock=True)
        self.monitor = Process(target=self.run,
                               args=(self.queueUp,
                                     self.queueDown,
                                     self.done,
                                     self.exitcode,                                         
                                     self.getURI))
        self.monitor.start()

    def isDone(self):
        return (self.done.value, self.exitcode.value)

    def getOutput(self):
        if not self.done.value:
            self.queueDown.put("GET_OUTPUT")
        try:
            result = self.queueUp.get(block=True, timeout=1)
        except Empty:
            raise NeXPyroError("Could not retrieve output!")
        return result

    def getURIfromQueue(self):
        try:
            result = self.queueUp.get(block=True, timeout=20)
        except Empty:
            raise NeXPyroError("Could not start Pyro service!")
        self.msg("result: " + result)
        if result.startswith("URI: "):
            self.uri = result.split()[1]
            return self.uri
        return None

    def account(self):
        return "%s@%s" % (self.user, self.host)

    def run(self, queueUp, queueDown, done, exitcode, getURI=False):
        self.dbg("Process PID: " + str(os.getpid()));
        argv = ["/usr/bin/ssh", "-tt", self.account()]
        if self.localPort != 0:
            argv.append("-L %i:localhost:%i" %
                        (self.localPort, self.remotePort))
        argv.append(self.command)
        pipe = self.make_pipe(argv)
        pipe.stdin.close()
        poller = select.poll()
        poller.register(pipe.stdout.fileno(), POLLIN)
        while True:
            L = []
            try:
                L = poller.poll(100)
            except KeyboardInterrupt:
                self.msg("Interrupted!")
            if len(L) > 0:
                if L[0][1] != POLLIN:
                    self.dbg("poll found error")
                    break
                line = pipe.stdout.readline()
                self.dbg("read: " + line.rstrip())
                self.output += line
                if getURI and line.startswith("URI: "):
                    queueUp.put(line)
            if not queueDown.empty():
                item = queueDown.get()
                if item == "TERMINATE":
                    break
                elif item == "GET_OUTPUT":
                    queueUp.put(self.output)
                else:
                    print "Strange queue item: ", item
                    sys.exit(1)
        self.dbg("terminating pipe")
        pipe.terminate()
        exitcode.value = pipe.wait()
        result = "exited with code: %i" % exitcode.value
        self.dbg(result)
        queueUp.put(self.output)
        done.value = True

    def make_pipe(self, argv):
        command = " ".join(argv)
        self.dbg("running: " + command)
        pipe = Popen(argv, bufsize=0,
                     stdin=PIPE, stdout=PIPE, stderr=STDOUT,
                     close_fds=True)
        self.dbg("Pipe PID: %i" % pipe.pid)
        return pipe

    def msg(self, m):
        print "NeXPyroSSH(%i) %s: %s" % (self.id, self.account(), str(m))

    # Enable debugging messages?
    debug = True

    def dbg(self, m):
        if self.debug == True:
            print "NeXPyroSSH(%i) %s: DBG: %s" % (self.id, self.account(), str(m))

    def terminate(self):
        self.dbg("terminate()")
        self.queueDown.put("TERMINATE")
        time.sleep(1)

class NeXPyroError(Exception):
    pass
