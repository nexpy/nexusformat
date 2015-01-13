
'''
LAUNCH.PY

Created on Jan 13, 2015

@author: wozniak
'''

import os, sys, time
from optparse import OptionParser

from nexusformat.pyro.session import NeXPyroSession

def sleepSafe(seconds):
    try: 
        time.sleep(seconds)
    except KeyboardInterrupt:
        print(" Interrupted!")
        sys.exit(1)

def crash(msg):
    print "launch: error: " + msg
    sys.exit(1)

def run_parser():
    global user, hostname, localPort, sessionTime
    print("parser...")
    parser = OptionParser()
    parser.add_option("-u", "--user", 
                      default=os.getenv("USER"), 
                      help="username on remote system, " + 
                           "defaults to USER in environment")
    parser.add_option("-H", "--hostname", dest="hostname", 
                      default="localhost",
                      help="the remote system hostname, " + 
                           "default localhost")
    parser.add_option("-p", "--localPort", 
                      default=9090,
                      help="the local port, default 9090")
    parser.add_option("-t", "--sessionTime", 
                      default=0,
                      help="session time (seconds), " + 
                           "0=forever (default)")
    (options, args) = parser.parse_args()
    user        = options.user
    hostname    = options.hostname
    localPort   = options.localPort
    sessionTime = options.sessionTime
    if len(args) > 0:
        crash("does not accept positional arguments!")

def run():
    global user, hostname, localPort, sessionTime
    run_parser()
    session = NeXPyroSession(user, hostname, localPort)
    b = session.run()
    if not b:
        crash("session could not be established!")
    if sessionTime != 0:
        sleepSafe(sessionTime)
        session.terminate()

if __name__ == '__main__':
    run()
