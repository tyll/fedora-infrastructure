#!/bin/bash
# Copyright (C) 2009 - Ricky Zhou ricky fedoraproject.org
#
# This program is free software; you can redistribute it and/or modify it 
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 or later.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA
#


if [ $# -lt 2 ]; then
    echo "Usage: $0 [name] [script]"
    exit 1;
fi

NAME=$1
SCRIPT=$2

LOCKDIR="/var/tmp/$NAME"
PIDFILE="$LOCKDIR/pid"

function cleanup {
    rm -rf "$LOCKDIR"
}

RESTORE_UMASK=$(umask -p)
umask 0077
if ! mkdir "$LOCKDIR"; then
    echo "$LOCKDIR already exists, exiting"
    PID=$(cat "$PIDFILE")
    if [ -n "$PID" ]; then
        echo "(pid $PID)"
    fi
    exit 1;
fi

trap cleanup EXIT SIGQUIT SIGHUP SIGTERM
echo $$ > "$PIDFILE"

$RESTORE_UMASK
eval "$SCRIPT"

