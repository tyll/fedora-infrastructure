#!/bin/bash
NETAPPMIB='/home/fedora/mmcgrath/netapp.mib'
COMMUNITY='public'
HOST='ntap-fedora1'

function get {
    snmpget -v 1 -Ov -m $NETAPPMIB -c $COMMUNITY $HOST $1 | awk -F": " '{ print $2 }'
}

echo "PHX"
echo -n "    Status: "
get .1.3.6.1.4.1.789.1.9.20.1.4.1
echo -n "    Lag: "
get .1.3.6.1.4.1.789.1.9.20.1.6.1
echo -n "    Mirror Timestamp: "
get .1.3.6.1.4.1.789.1.9.20.1.14.1
echo -n "    Last Transfer Size (MB): "
get .1.3.6.1.4.1.789.1.9.20.1.17.1
echo -n "    Last Transfer Time (seconds): "
get .1.3.6.1.4.1.789.1.9.20.1.18.1

echo "TPA"
echo -n "    Status: "
get .1.3.6.1.4.1.789.1.9.20.1.4.2
echo -n "    Lag: "
get .1.3.6.1.4.1.789.1.9.20.1.6.2
echo -n "    Mirror Timestamp: "
get .1.3.6.1.4.1.789.1.9.20.1.14.2
echo -n "    Last Transfer Size (MB): "
get .1.3.6.1.4.1.789.1.9.20.1.17.2
echo -n "    Last Transfer Time (seconds): "
get .1.3.6.1.4.1.789.1.9.20.1.18.2


