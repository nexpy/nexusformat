#!/bin/bash 

set -eu

shopt -s huponexit

DIR=$( dirname $0 )
python ${DIR}/start_server.py &
wait 
echo start_server waited
