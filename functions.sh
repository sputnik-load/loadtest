#!/bin/bash

[ -z "${AMMO_DIR}" ] && AMMO_DIR=/data/qa/ammo
[ -z "${REMOTE_SOURCE}" ] && REMOTE_SOURCE="<DEFAULT_AMMO_HOST>"


function _find_file() {
    local name=$1
    exit_error=$2
    (( _MAX_LEVEL = _MAX_LEVEL - 1 ))
    if [ ${_MAX_LEVEL} -le 0 ]; then
	echo "File not found '$name'"
	if [ "$exit_error" = "1" ]; then
	    exit 1
	else
    	    return
	fi
    fi
    [ -s "$name" ] && result=$name || _find_file "../$name" "$exit_error"
}

MAX_LEVEL=7
# find_file "common.ini"
# ищет файл $1 начиная от текущей папки и поднимаясь выше
# до тех пор пока не найдет указанный файл или не достигнет MAX_LEVEL
# результат помещает в переменную $result + возвращает соответствующий exit code
function find_file() {
    _MAX_LEVEL=${MAX_LEVEL}
    result=""
    _find_file "$1" "$2"
}

function get_data_file() {
    local fname=$1
    local fpath=${AMMO_DIR}/$1
    if [ ! -s "$fpath" ]; then
	scp "${REMOTE_SOURCE}:$fpath" "${AMMO_DIR}/"
    else # TODO: rsync
	echo "File '$fpath' already exist"
    fi
    [ -s "$fpath" ] && return 0 || return 1
}
