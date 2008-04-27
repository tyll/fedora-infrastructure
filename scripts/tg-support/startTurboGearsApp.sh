#!/bin/bash
# Starts a turbogears application

if [ ! $1 ]
then
    echo "Please provide a path to the turbogears startup file and an optional environment"
    exit 1
fi

DIR=$(/usr/bin/dirname $1)
cd $DIR
pkill -f "python $1 $2"

exec /usr/bin/python $1 $2

