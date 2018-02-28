#!/bin/bash

pids=$(ps -ef | grep api-server | awk '$9~/yandex-tank-api-server$/ {print $2}')
echo "Yandex-tank-api-server active pids are "$pids"."
kill $pids
echo "Yandex-tank-api-server has been restarted."
sleep 3
pids=$(ps -ef | grep api-server | awk '$9~/yandex-tank-api-server$/ {print $2}')
echo "Yandex-tank-api-server active pids are "$pids"."
