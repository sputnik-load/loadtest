#!/bin/bash


PATCHREV='.post6'
PYTHON=python2.7


function update_tank() {
    git clone https://github.com/yandex/yandex-tank.git
    cd yandex-tank
    git reset --hard e1890687ef661de2d0388566c7a63b54e57c94c0 # временно фиксируемся на коммите от 16 фев 2016г - последний коммит перед началом глобальной переделки yandex-tank
    sed -i "s/version='\([\.0-9]*\)',/version='\1${PATCHREV}',/g" setup.py  # правим номер версии на Post-release N
    cat ../yandex-tank-patches/*.patch | patch -p1
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf yandex-tank
}


function update_tank_api() {
    git clone https://github.com/yandex-load/yandex-tank-api.git
    cd yandex-tank-api
#    git checkout dev ##OPTIONAL
    cat ../yandex-tank-api-patches/*.patch | patch -p1
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf yandex-tank-api
}


function update_tank_api_client() {
    git clone https://github.com/yandex-load/yandex-tank-api-client.git
    cd yandex-tank-api-client
    #cat ../yandex-tank-api-client-patches/*.patch | patch -p1
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf yandex-tank-api-client
}


function update_yatank_online() {
    git clone https://github.com/yandex-load/yatank-online.git 
    cd yatank-online
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf yatank-online
}


function update_django_qunit() {
    git clone https://github.com/sputnik-load/django-qunit.git 
    cd django-qunit 
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf django-qunit
}


function update_yatank_report() {
    git clone https://github.com/sputnik-load/yatank-report.git
    cd yatank-report
    pip2pi /data/qa/pypiserver/packages/ --index-url=https://pypi.python.org/simple/ --normalize-package-names -z -r requirements.txt
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf yatank-report
}


function update_yatank_mail() {
    git clone https://github.com/sputnik-load/yatank-mail.git
    cd yatank-mail
    pip2pi /data/qa/pypiserver/packages/ --index-url=https://pypi.python.org/simple/ --normalize-package-names -z -r requirements.txt
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf yatank-mail
}


function update_yatank_collect() {
    git clone https://github.com/krylov/yatank-collect.git
    cd yatank-collect
    pip2pi /data/qa/pypiserver/packages/ --index-url=https://pypi.python.org/simple/ --normalize-package-names -z -r requirements.txt
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf yatank-collect
}


function update_yatank_sputnikonline() {
    git clone https://github.com/sputnik-load/yatank-sputnikonline.git
    cd yatank-sputnikonline
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf yatank-sputnikonline
}


function update_yatank_hipchat() {
    git clone https://github.com/sputnik-load/yatank-hipchat.git
    cd yatank-hipchat
    pip2pi /data/qa/pypiserver/packages/ --index-url=https://pypi.python.org/simple/ --normalize-package-names -z -r requirements.txt
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf yatank-hipchat
}


function update_yatank_salts() {
    git clone https://github.com/sputnik-load/yatank-salts.git
    cd yatank-salts
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf yatank-salts
}


function update_ammo() {
    git clone https://github.com/maklaut/ammo
    cd ammo
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf ammo
}


function update_runload() {
    git clone https://github.com/sputnik-load/run-load.git
    cd run-load
    pip2pi /data/qa/pypiserver/packages/ --index-url=https://pypi.python.org/simple/ --normalize-package-names -z -r requirements.txt
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf run-load
}

function update_salts_tank() {
    git clone https://github.com/sputnik-load/salts-tank.git
    cd salts-tank
    pip2pi /data/qa/pypiserver/packages/ --index-url=https://pypi.python.org/simple/ --normalize-package-names -z -r requirements.txt
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf salts-tank
}

function update_yatank_graphite() {
    git clone https://github.com/sputnik-load/yatank-graphite.git
    cd yatank-graphite
    pip2pi /data/qa/pypiserver/packages/ --index-url=https://pypi.python.org/simple/ --normalize-package-names -z -r requirements.txt
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf yatank-graphite
}

function update_yatank_vegeta() {
    git clone https://github.com/sputnik-load/yatank-vegeta.git
    cd yatank-vegeta
    pip2pi /data/qa/pypiserver/packages/ --index-url=https://pypi.python.org/simple/ --normalize-package-names -z -r requirements.txt
    $PYTHON setup.py sdist upload -r internal
    cd ..
    rm -rf yatank-vegeta
}

function update_requirements() {
    sudo pip install --upgrade pip2pi
    export PATH=$PATH:/usr/pgsql-9.4/bin
    pip2pi /data/qa/pypiserver/packages/ --index-url=https://pypi.python.org/simple/ --normalize-package-names -z -r requirements.txt
}

if [[ -z $* ]]; then
	echo "No options found!" >&2
	exit 1
fi


usage() {
	local packages="tank|tank_api|tank_api_client"
	packages="$packages|yatank_salts|yatank_online|yatank_report"
	packages="$packages|yatank_hipchat|yatank_sputnikonline|ammo"
	packages="$packages|runload|salts_tank|requirements|yatank_collect|yatank_mail"
	packages="$packages|yatank_graphite|yatank_vegeta|django_qunit"
	echo "Usage: $0 -p <$packages> [-h]" >&2
	exit 1
}


while getopts "p:h" opt
do
case $opt in
	p) PACKAGE_NAME=$OPTARG
		;;
	h) usage
		;;
	*) usage
		;;
esac
done


if [ -z ${PACKAGE_NAME+x} ]; then
	echo "PACKAGE_NAME is not given." >&2
	usage
fi

source /data/qa/ltbot/venv/bin/activate
[ $? -ne 0 ] && echo "Virtual env 'venv' has not been activated successfully." && exit 1

update_$PACKAGE_NAME
exit 0
