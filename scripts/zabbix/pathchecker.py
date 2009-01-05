import os,sys

files = sys.argv[1:]
if not files:
    print "you must specify a file"
    sys.exit(1)
for file in files:
    if os.access(file, os.R_OK):
        print 1
    else:
        print 0
