#!/bin/bash

while [ -a /data/qa/ltbot/loadtest/update.lock ]
do
    echo "Запуск заблокирован: устанавливаются новые версии плагинов..."
    sleep 3
done

[ $# -eq 0 ] && echo "Config path isn't provided" && exit 1

config=$1  # ini-файл yandex-tank
[ ! -s "$config" ] && echo "Config '$config' not found" && exit 1

force=0
if [ $# -eq 2 ]; then
  if [ $2 == "--force" -o $2 == "-f" ]; then 
    echo "Force run has been enabled"
    force=1
  fi
fi

VENV=/data/qa/ltbot/venv
LOCK_DIR=/data/qa/_results/
CONSOLE_LOG=tank-console.log
TANK=${VENV}/bin/yandex-tank

GIT_ROOT="$(git rev-parse --show-toplevel)"
FUNCS=$GIT_ROOT/functions.sh && [ -x "$FUNCS" ] && source "$FUNCS"


VENV_ACTIVATE="${VENV}/bin/activate"
[ ! -s "${VENV_ACTIVATE}" ] && echo "Error: ${VENV_ACTIVATE} not found" && exit 1
source ${VENV_ACTIVATE}
EXIT_CODE_FILE=$(mktemp)

function finish {
  echo Deactivate VENV
  deactivate # VENV
  [ -f "${EXIT_CODE_FILE}" ] && rm -fv "${EXIT_CODE_FILE}"
}
trap finish EXIT

iter_number=$(grep -oE "\[.*phantom.*\]" $config | wc -l)  # считаем число секций [phantom]

for iter in $(seq 1 $iter_number)
do
    ammofile=$(sed -ne "s/^[ \t]*ammofile=\(.\+\)/\1/p" $config | sed "${iter}q;d")  # достаем путь к ammo-файлу из опции ammofile в текущей секции [phantom]
    AMMO_FILE=$(basename "$ammofile")
    export AMMO_DIR=$(dirname "$ammofile")  # если не указать AMMO_DIR, то по умолчанию будет использоваться /data/qa/ammo

#    get_data_file "${AMMO_FILE}"
#    [ $? -ne 0 ] && echo "Download error '${AMMO_DIR}/${AMMO_FILE}'" && exit 1
done

echo -e `date`"\t$0\t$*" >> run.log

find_file "common.ini" 1
common_ini=$result

find_file "run.sh.ini"
[ -r "$result" ] && . "$result"

hostvalue=$(hostname)

[ -f "${CONSOLE_LOG}" ] && mv "${CONSOLE_LOG}" "${CONSOLE_LOG}.bak"

find_file "scen_path.py"
scen_path_py=$result
scenario_path=$(python $scen_path_py -r $0 -c $config)
set -x
script -c "${TANK} --lock-dir \"${LOCK_DIR}\" -c $config -o \"salts.scenario_path=$scenario_path\" -o \"salts_report.force_run=$force\"; echo EXIT_CODE=\$? > ${EXIT_CODE_FILE}" "${CONSOLE_LOG}"
source ${EXIT_CODE_FILE}
set +x

artifacts_dir=$(grep -F 'INFO: Artifacts dir:' "${CONSOLE_LOG}" | sed -e 's/^.*INFO: Artifacts dir: \([^\r\n]*\)/\1/g' | tr -d '\r\n')
mv -v "${CONSOLE_LOG}" "${artifacts_dir}"/
mv -v _respon* "${artifacts_dir}"/
mv -v _error* "${artifacts_dir}"/
mv -v testResults.txt "${artifacts_dir}"/

find_file "utils/salts_import_files.py" 1
import_files=$result

salts_api_url=$(grep api_url ${artifacts_dir}/lunapark* | sed 's/api_url *= *//')
if [ -z "${salts_api_url}" ]
then
    salts_api_url="http://<salts-server>/api2/"
fi
echo "SALTS API URL: ${salts_api_url}"
python "${import_files}" -c "${common_ini}" -d "${artifacts_dir}"
