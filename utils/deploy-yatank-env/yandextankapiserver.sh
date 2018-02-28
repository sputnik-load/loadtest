#!/bin/bash

while [ -a /data/qa/ltbot/loadtest/update.lock ]
do
    echo "Запуск заблокирован: устанавливаются новые версии плагинов..."
    sleep 3
done

source /data/qa/ltbot/venv/bin/activate
python /data/qa/ltbot/venv/bin/yandex-tank-api-server --ignore-machine-defaults --log /data/qa/logs/api/yandex-tank-api-server.log --debug --work-dir /data/qa/_results/api/
deactivate
