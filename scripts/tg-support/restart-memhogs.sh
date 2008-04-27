#!/bin/sh
# Author: Toshio Kuratomi <toshio@fedoraproject.org>
# Script to restart supervisor controlled applications if their memory usage
# goes over a preset limit.
#
# This script is run on alternate app servers, checking the memory usage of
# each app.  If they exceed the maximum memory we've alloted to them, the
# script tells supervisor to restart the app.

# APPS and MEMLIMIT map a supervisor appname to a maximal memory usage.
# Note: Only put load balanced apps managed by TG in this var.
APPS=('mirrorlist_server' 'mirrormanager' 'packagedb' 'smolt' 'fas')
MEMLIMIT=(250000          800000          500000      200000  1000000)
# These aren't load balanced yet
#APPS=("${APPS[@]}" 'transifex' 'bodhi')
#MEMLIMIT=(${MEMLIMIT[@]} 250000 500000)

for ((i = 0 ; i < ${#APPS[@]} ;i++ )) ; do
  # Supervisor knows the PID of the processes
  PID=`supervisorctl status ${APPS[$i]} | sed -e 's/.*pid \([0-9]\+\),.*/\1/'`
  # Ignore crashed apps or apps not present on this server
  if test `echo "$PID" | egrep '^[0-9]+$'` ; then
    # We use Resident Set Size to determine if the app is using too much memory
    RSS=`ps -eo pid,rss|egrep -w "^[[:space:]]*$PID"| awk '// { print $2 }'`
    if test "$RSS" -gt ${MEMLIMIT[$i]} ; then
      # Use supervisor to restart the app
      echo "Restarting ${APPS[$i]} $PID RSS: $RSS"
      supervisorctl restart ${APPS[$i]}
    fi
  fi
done
