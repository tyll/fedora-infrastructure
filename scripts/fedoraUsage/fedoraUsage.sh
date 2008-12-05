#!/bin/bash

function updateIps {
    release=$1
    YESTERDAY=`/bin/date -d yesterday +%Y-%m-%d`
    YEAR=`/bin/date -d yesterday +%Y`
    MONTH=`/bin/date -d yesterday +%m`
    DAY=`/bin/date -d yesterday +%d`

    /bin/mkdir -p /srv/web/fedoraUsage.private
    /bin/awk /$release/'{ print $1 }' /var/log/hosts/proxy*/$YEAR/$MONTH/$DAY/http/mirrors.fedoraproject.org-access.log | /bin/sort -u > /srv/web/fedoraUsage.private/$release.tmp
    /bin/sort -u /srv/web/fedoraUsage.private/$release.tmp /srv/web/fedoraUsage.private/$release.ips > /srv/web/fedoraUsage.private/$release.ips.new
    /bin/mv /srv/web/fedoraUsage.private/$release.ips.new /srv/web/fedoraUsage.private/$release.ips
    /usr/bin/wc -l /srv/web/fedoraUsage.private/$release.ips > /srv/web/fedoraUsage/$release
}

updateIps rawhide
updateIps updates-released-fc6
updateIps updates-released-f7
updateIps updates-released-f8
updateIps updates-released-f9
updateIps updates-released-f10

