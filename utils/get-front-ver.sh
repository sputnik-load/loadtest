#!/bin/bash -x

ini=$1

[ ! -f "$ini" ] && echo File '$ini' not found && exit 1

address=$(sed -ne "s/^[ \t]*address=\([-a-zA-Z0-9\.:]\+\).*/\1/p" $ini)

curl -m 3 -si http://$address | grep -F X-Version | awk '{print $2}'
