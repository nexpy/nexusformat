
import os, time
import select
from select import POLLIN
from multiprocessing import Process, Queue
from subprocess import Popen, PIPE, STDOUT

_ssh_process_id = 0

class NeXpyroSSH:

    def __init__(self, user, host,
                 hours=1, localPort=0, remotePort=0,
                 command=None, getURI=False):

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

        self.queue = Queue()
        self.process = Process(target=self.run, args=(self.queue,))
        self.process.start()
        if getURI:
            result = self.queue.get(block=True, timeout=20)
            self.msg("result: " + result)
            if result.startswith("URI: "):
                self.uri = result.split(" ")[1]

    def account(self):
        return "%s@%s" % (self.user, self.host)

    def run(self, queue):
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
                if queue != None and line.startswith("URI: "):
                    queue.put(line)
            if not queue.empty():
                item = queue.get()
                if item == "TERMINATE":
                    break
        self.dbg("terminating pipe")
        pipe.terminate()
        exitcode = pipe.wait()
        result = "exited with code: %i" % exitcode
        self.dbg(result)
        queue.put(result)

    def make_pipe(self, argv):
        command = " ".join(argv)
        self.dbg("running: " + command)
        pipe = Popen(argv, bufsize=0, 
                     stdin=PIPE, stdout=PIPE, stderr=STDOUT, 
                     close_fds=True)
        self.dbg("Pipe PID: %i" % pipe.pid)
        return pipe

    def msg(self, m):
        print "NeXpyroSSH(%i) %s: %s" % (self.id, self.account(), str(m))

    # Enable debugging messages?
    debug = True

    def dbg(self, m):
        if self.debug == True:
            print "NeXpyroSSH(%i) %s: DBG: %s" % (self.id, self.account(), str(m))

    def terminate(self):
        self.dbg("terminate()")
        self.queue.put("TERMINATE")
        time.sleep(1)
        self.process.terminate()
