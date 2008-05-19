#!/bin/bash

for f in `find -type f | grep attachment`
do
    dest=`echo $f | sed -e 's,/attachments,,' -e 's,./,,' -e 's/(2f)/_/' -e 's,/,_,g'`
    src=$f
    echo "/root/mw-upload.py '$src' '$dest'"
done
