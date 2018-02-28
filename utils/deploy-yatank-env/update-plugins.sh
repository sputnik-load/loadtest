#!/bin/bash


test_ssh_connection() {
	local hosts=("$@")
	tanks=()
	for item in "${hosts[@]}"
	do
		echo "--- Test ssh connection for $item host ---"
		nc -z -v -w5 $item 22
		if [[ $? -eq 0 ]]
		then
			tanks+=($item)
		fi
		echo "---"
	done
}


PIP_VERSION=7.1.2
VENV_PATH=/data/qa/ltbot
VENV_NAME=venv
PIP_HOSTNAME=<DEFAULT_PyPI_HOST>
PIP_OPTS="--upgrade --no-cache-dir --index-url http://$PIP_HOSTNAME:8080/simple/ --trusted-host $PIP_HOSTNAME"
TANKS_FILE=tanks
REQUIREMENTS_FILES=(yandextank_requirements.txt util_requirements.txt plugins_requirements.txt common_requirements.txt)
PSSH=pssh
TEST=0


tanks=( $( cat $TANKS_FILE ) )
requirements=( $( cat ${REQUIREMENTS_FILES[@]} ) )


if [[ $# -ge 1 ]]
then
	tanks=($1)
fi

test_ssh_connection "${tanks[@]}"

if [[ $# -ge 2 ]]
then
	if [[ $2 == "test" ]]
	then
		TEST=1
		PSSH=parallel-ssh   # for Ubuntu: parallel-ssh is used instead of pssh
	fi
fi

if [[ $# -eq 3 ]]
then
	VENV_NAME=$3
fi

VENV_PATH="$VENV_PATH/$VENV_NAME"

if [[ $TEST -eq 1 ]]
then
	SSH_COMMAND="source $VENV_PATH/bin/activate"
	SSH_COMMAND="$SSH_COMMAND && pip install ${PIP_OPTS} ${requirements[@]}"
else
	SSH_COMMAND="sudo chmod g+rwX -R $VENV_PATH;"
	SSH_COMMAND="$SSH_COMMAND sudo chgrp load-test -R $VENV_PATH ;"
        SSH_COMMAND="$SSH_COMMAND source $VENV_PATH/bin/activate"
	SSH_COMMAND="$SSH_COMMAND && pip install ${PIP_OPTS} pip==$PIP_VERSION"
	SSH_COMMAND="$SSH_COMMAND && pip install ${PIP_OPTS} ${requirements[@]}"
fi

ssh_commands=()
for item in "${tanks[@]}"
do
	ssh_commands+=("$PSSH -H $item -t 0 -i $SSH_COMMAND")
done

echo "The following commands will be executed:"
i=0
for item in "${tanks[@]}"
do
	echo "*** $item ***"
	echo ${ssh_commands[$i]}
	echo "***********"
	i=$((i+1))
done

read -p "Are you sure? If it is YES press 'y' or 'Y'... " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
	i=0
	for item in "${tanks[@]}"
	do
		echo "*** $item ***"
		${ssh_commands[$i]}
		i=$((i+1))
	done
fi
