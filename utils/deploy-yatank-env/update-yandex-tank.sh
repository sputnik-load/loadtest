#!/bin/bash -x
PYPI_HOST="<DEFAULT_PyPI_HOST>"
HOSTS="-H host-3 -H host-2 -H host-3"
PIP_OPTS="--upgrade --no-cache-dir --index-url http://${PYPI_HOST}:8080/simple/ --trusted-host "
PKGS="runload yandextank yandex-tank-api yatank-report yatank-salts yatank-sputnikonline yatank-mail yatank-hipchat tornado==4.0.0 python-daemon pyjade==3.0.0 hypchat==0.15"

echo pssh $HOSTS -i "sudo chmod g+rwX -R /data/qa/ltbot/venv; sudo chgrp load-test -R /data/qa/ltbot/venv ; source /data/qa/ltbot/venv/bin/activate  &&  pip install ${PIP_OPTS} $PKGS"
