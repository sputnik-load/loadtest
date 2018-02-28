#!/bin/bash -x

HOSTS="host-1 host-2 host-3"
REPO_DIR=/data/qa/loadtest
REMOTE_LT_DIR=/data/qa/ltbot/loadtest

for host in $HOSTS; do scp $REPO_DIR/utils/ltdeploy.py $host:$REMOTE_LT_DIR/ltdeploy.py; done
for host in $HOSTS; do scp $REPO_DIR/utils/pip-install-packages.sh $host:$REMOTE_LT_DIR/pip-install-packages.sh; done
ssh $HOSTS "source /data/qa/ltbot/venv/bin/activate && $REMOTE_LT_DIR/ltdeploy.py -e $REMOTE_LT_DIR/pip-install-packages.sh"
