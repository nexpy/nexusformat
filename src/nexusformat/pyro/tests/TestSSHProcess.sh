#!/bin/bash

# set -x
set -eu

THIS=$( dirname $0 )
SRC=$( cd ${THIS}/../../.. ; /bin/pwd )

export PYTHONPATH=${SRC}
python ${THIS}/TestSSHProcess.py
