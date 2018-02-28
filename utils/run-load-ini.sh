#!/bin/bash

VENV_PATH=/data/qa/ltbot/venv
LT_PATH=/data/qa/ltbot/loadtest/
LOAD_INI=search/s_collector/debug/load_debug_phantom.ini
SERVER_RESULT_PATH=/data/qa/_results/api/
LOG_PATH=.
YATANKAPI_HOST=salt-dev

source $VENV_PATH/bin/activate
runload -g -p $LT_PATH/$LOAD_INI -l $LOG_PATH/runload.log -s $YATANKAPI_HOST -r 8888
deactivate
