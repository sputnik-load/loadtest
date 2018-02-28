#!/bin/bash


PYTHON=/usr/bin/python2.7
PIP_HOSTNAME=<DEFAULT_PyPI_HOST>
PIP_OPTS="--upgrade --no-cache-dir --index-url http://$PIP_HOSTNAME:8080/simple/ --trusted-host $PIP_HOSTNAME"


if [[ -z $* ]]; then
	echo "No options found!" >&2
	exit 1
fi

usage() {
	echo "Command to execute: pip install ${PIP_OPTS} RunLoad}"
	echo "Usage: $0 -d VIRTUALENVS DIR PATH -v VENV NAME [-h]" >&2
	exit 1
}

while getopts "d:v:h" opt
do
case $opt in
	d) VENV_PATH=$OPTARG
		;; 
	v) VENV_NAME=$OPTARG
		;; 
	h) usage
		;;
	*) usage
		;; 
esac
done

if [ -z ${VENV_PATH+x} ]; then
	echo "VIRTUALENVS DIR PATH is not given." >&2
	usage
fi

if [ -z ${VENV_NAME+x} ]; then
	echo "VENV NAME is not given." >&2
	usage
fi

venv_dir=$VENV_PATH/$VENV_NAME
venv_act="source $venv_dir/bin/activate"

$venv_act
if [[ $? -ne 0 ]]; then
	echo "Virtual env has not been activated. It will be created."
	rm -rf $venv_dir
	virtualenv --python=$PYTHON $venv_dir
	$venv_act
	[ $? -ne 0 ] && echo "Virtual env $VENV_NAME cannot be activated." && exit 1
fi
pip install ${PIP_OPTS} ${requirements[@]}
[ $? -ne 0 ] && echo "RunLoad has not been installed successfully." && exit 1

echo "RunLoad has been installed successfully."
exit 0
