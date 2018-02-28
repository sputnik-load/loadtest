#!/bin/bash

[ -z "$1" -o -z "$2" ] && echo -e "Check tcp connection to target host from all local ip's.\nUsage:\n\t./check-iface-access.sh <target_host> <host_for_header>" && exit 1

TANK_IPS=$(/sbin/ifconfig | grep -oE 'inet addr:10\.[0-9\.]*' | sed -e 's/inet addr://g')
ADDRESS=$1
HOST_HEADER=$2
for ip in ${TANK_IPS} ; do
    echo -ne "$ip "
    curl --connect-timeout 3 --interface $ip -H "Host: ${HOST_HEADER}" $ADDRESS -sS > /dev/null && echo Ok
done

