#!/bin/bash -eu

# RUN-LOCAL
# Run a client/server connection locally

NEXPYRO=$( cd $( dirname $0 ) ; /bin/pwd )
DAEMON=${NEXPYRO}/nxfileservice.py
# CLIENT=${NEXPYRO}/client.py
CLIENT=${NEXPYRO}/nxfr_test.py
# DAEMON=${NEXPYRO}/TestService1.py
# CLIENT=${NEXPYRO}/TestClient1.py

NEXPY_SRC=$( cd ${NEXPYRO}/.. ; /bin/pwd )

PYTHON="python -u"
export PYTHONPATH=${NEXPY_SRC}

ARGS=${*}

message()
{
  echo "run.sh: ${*}"
}

# Start daemon
TMPFILE=$( mktemp )
echo "TMPFILE=${TMPFILE}"
( ${PYTHON} ${DAEMON} | tee ${TMPFILE} | sed 's/^/S: /' 2>&1 ) &
DAEMON_PID=${!}
message "Daemon running: pid: ${DAEMON_PID}"
# echo "DAEMON_PID: ${DAEMON_PID}"

shutdown_daemon()
{
  PID=$1
  echo "Killing: ${PID}"
  kill ${PID} || true
  sleep 1
  kill -s KILL ${PID} || true
}

# Obtain daemon URI
sleep 1
URI=$( grep "URI:" ${TMPFILE} | cut -d ' ' -f 2 )
if [[ ${URI} != PYRO* ]]
then
  echo "Daemon startup failed!"
  shutdown_daemon ${DAEMON_PID}
  echo "contents of: ${TMPFILE}"
  cat ${TMPFILE}
  exit 1
fi
echo "URI: ${URI}"

# Start client in different directory (/tmp)
if ! ( cd /tmp ; ${PYTHON} ${CLIENT} ${ARGS} ${URI} )
then
  message "Client failed!"
fi

# rm ${TMPFILE}
wait
exit 0
