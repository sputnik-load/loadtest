#!/bin/bash -x
sed -i -e 's/plugin_\(.*\)=Tank\/Plugins\/\(.*\)\.py/plugin_\1=yandextank.plugins.\2/g' "$1"
