#!/bin/bash


TANKS=tanks
REQFILES=(util_requirements.txt plugins_requirements.txt)
NO_STRICT_SSH="ssh -o StrictHostKeyChecking=no"
NO_STRICT_SCP="scp -o StrictHostKeyChecking=no"
VIRTUALENV_BIN="/data/qa/ltbot/venv/bin"
LTPATH="/data/qa/ltbot/loadtest"
SALTS_HOST="<DEFAULT_SALTS_HOST>"


test_ssh_connection() {
	local hosts=("$@")
	tankhosts=()
	for item in "${hosts[@]}"
	do
		echo "--- Test ssh connection for $item host ---"
		nc -z -v -w5 $item 22
		if [[ $? -eq 0 ]]
		then
			tankhosts+=($item)
		fi
		echo "---"
	done
}

test_supervisor() {
	local hosts=("$@")
	tankhosts=()
	wos_tankhosts=()
	for item in "${hosts[@]}"
	do
		echo "--- Test supervisor for $item host ---"
		svrd_exist=$( $NO_STRICT_SSH $item "[ -f $VIRTUALENV_BIN/supervisord ] && echo 't' || echo 'f'" )
		svrctl_exist=$( $NO_STRICT_SSH $item "[ -f $VIRTUALENV_BIN/supervisorctl ] && echo 't' || echo 'f'" )
		if [ $svrd_exist == "t" ] && [ $svrctl_exist == "t" ]
		then
			echo "Supervisor found."
			tankhosts+=($item)
		else
			echo "Supervisor not found."
			wos_tankhosts+=($item)
		fi
		echo "---"
	done
}

copy_supervisor_configs() {
	svr_path=$LTPATH/utils/supervisor
	configs=($(ls $svr_path/tank-*.ini))
	local hosts=("$@")
	for tank_host in "${hosts[@]}"
	do
		echo "--- Copy supervisor configs on the $tank_host host ---"
		$NO_STRICT_SCP $svr_path/supervisord.conf $tank_host:/tmp/
		$NO_STRICT_SSH $tank_host "sudo mv /tmp/supervisord.conf /etc/"

		$NO_STRICT_SSH $tank_host "sudo rm -rf /etc/supervisord.d"
		$NO_STRICT_SSH $tank_host "sudo mkdir /etc/supervisord.d"

		for config in "${configs[@]}"
		do
			$NO_STRICT_SCP $config $tank_host:/tmp/
			fname=${config#$svr_path/}
			$NO_STRICT_SSH $tank_host "sudo mv /tmp/$fname /etc/supervisord.d/"
		done		
		$NO_STRICT_SCP $LTPATH/utils/deploy-yatank-env/yandextankapiserver.sh $item:$VIRTUALENV_BIN/
	done

	echo "--- Copy celery configs for supervisor on the $SALTS_HOST SALTS host ---"
	configs=($(ls $svr_path/salt-*.ini))
	for config in "${configs[@]}"
	do
		$NO_STRICT_SCP $config $SALTS_HOST:/tmp/
		fname=${config#$svr_path/}
		$NO_STRICT_SSH $SALTS_HOST "sudo mv /tmp/$fname /etc/supervisord.d/"
	done		
}


restart_supervisor() {
	local hosts=("$@")
	for item in "${hosts[@]}"
	do
		echo "--- Restart supervisor on the $item host ---"
		$NO_STRICT_SSH $item "sudo $VIRTUALENV_BIN/supervisorctl shutdown"
		$NO_STRICT_SSH $item "sudo $VIRTUALENV_BIN/supervisord -c /etc/supervisord.conf"
		$NO_STRICT_SCP $LTPATH/utils/deploy-yatank-env/restart-yatankapi.sh $item:$VIRTUALENV_BIN/
		$NO_STRICT_SSH $item "sudo $VIRTUALENV_BIN/restart-yatankapi.sh"
	done
}

show_supervisor_status() {
	local hosts=("$@")
	for item in "${hosts[@]}"
	do
		echo "--- Show supervisor status for the $item host ---"
		$NO_STRICT_SSH $item "sudo $VIRTUALENV_BIN/supervisorctl status"	
	done
}


records=( $( cat ${REQFILES[@]} ) )
tankhosts=( $( cat $TANKS ) )

echo "***** Test ssh connection for tank hosts *****"
test_ssh_connection "${tankhosts[@]}"
echo "Tank Hosts with SSH: ${tankhosts[@]}"
echo


echo "***** Test supervisor for tank hosts *****"
test_supervisor "${tankhosts[@]}"
echo "Tank Hosts with supervisor: ${tankhosts[@]}"
echo "Tank Hosts without supervisor: ${wos_tankhosts[@]}"
echo

echo "***** Copy supervisor configs *****"
copy_supervisor_configs "${tankhosts[@]}"
echo

echo "***** Restart supervisor *****"
restart_supervisor "${tankhosts[@]}"
echo

sleep 3
echo "***** Show supervisor status *****"
show_supervisor_status "${tankhosts[@]}"
echo

