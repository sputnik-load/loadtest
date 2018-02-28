#!/bin/bash

hostname --fqdn
ifconfig | grep -oE inet\ addr:\([0-9]+\.\){4} | sed 's/inet addr://' | head -n -1 | xargs echo
