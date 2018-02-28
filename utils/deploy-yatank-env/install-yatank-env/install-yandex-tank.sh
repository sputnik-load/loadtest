#!/bin/bash
VENV_PATH=/data/qa/ltbot/venv
[ -n "$1" ] && VENV_PATH=$1
PYTHON=/usr/bin/python2.7
PIP=pip2.7

set -x
PYPI_HOST=<DEFAULT_PYPI_HOST>
PYPI_URL=http://${PYPI_HOST}:8080/simple/
PIP_OPTS="--trusted-host ${PYPI_HOST} --index-url ${PYPI_URL} --upgrade"
REQUIREMENTS=$(dirname $0)/prepare-pip-repo/requirements.txt
set +x

[ -e "${VENV_PATH}" ] && echo "Path already exists VENV_PATH=${VENV_PATH}" && exit 1

deactivate > /dev/null  2>&1
virtualenv --python=$PYTHON ${VENV_PATH}
source ${VENV_PATH}/bin/activate
$PIP install --index-url ${PYPI_URL} --upgrade pip
export PATH=$PATH:/usr/pgsql-9.4/bin
$PIP install ${PIP_OPTS} yandextank yandex-tank-api yandex-tank-api-client yatank-online==0.0.3 ammo yatank-report yatank-sputnikonline yatank-mail yatank-hipchat -r ${REQUIREMENTS}
#$PIP install ${PIP_OPTS} psycopg2
deactivate

wget -c http://${PYPI_HOST}/static/phantom.tar.gz
tar zxf phantom.tar.gz -C /data/qa
rm -vf phantom.tar.gz

JMETER_VERSION="2.13"
wget -c http://${PYPI_HOST}/static/apache-jmeter-${JMETER_VERSION}.tar.gz
tar zxf apache-jmeter-2.13.tar.gz -C /data/qa
rm -vf apache-jmeter-2.13.tar.gz
