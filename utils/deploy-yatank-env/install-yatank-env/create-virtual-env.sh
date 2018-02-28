#!/bin/bash

[ $# -eq 0 ] && echo "Venv name isn't provided" && exit 1

VENV_PATH=/data/qa/ltbot/$1
PYTHON=/usr/bin/python2.7

deactivate > /dev/null  2>&1
virtualenv --python=$PYTHON $VENV_PATH
source ${VENV_PATH}/bin/activate
