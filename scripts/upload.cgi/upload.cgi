#!/usr/bin/python
#
# CGI script to handle file updates for the rpms CVS repository. There
# is nothing really complex here other than tedious checking of our
# every step along the way...
#
# License: GPL

import os
import sys
import cgi
import tempfile
import grp
try:
    import hashlib
    md5_constructor = hashlib.md5
except ImportError:
    import md5
    md5_constructor = md5.new

# Reading buffer size
BUFFER_SIZE = 4096

# We check modules exist from this dircetory
CVSREPO = '/cvs/pkgs/rpms'

# Lookaside cache directory
CACHE_DIR = '/srv/cache/lookaside/pkgs'

# Fedora Packager Group
PACKAGER_GROUP = 'packager'

def send_error(text):
    print 'Content-type: text/plain'
    print
    print text
    sys.exit(1)

def check_form(form, var):
    if not form.has_key(var):
        send_error('Required field "%s" is not present.' % var)
    ret = form.getvalue(var)
    if isinstance(ret, list):
        send_error('Multiple values given for "%s". Aborting.' % var)
    return ret

os.umask(002)

authenticated = False

if os.environ.has_key('SSL_CLIENT_S_DN_CN'):
    auth_username = os.environ['SSL_CLIENT_S_DN_CN']
    if auth_username in grp.getgrnam(PACKAGER_GROUP)[3]:
        authenticated = True

if not authenticated:
    print 'Status: 403 Forbidden'
    print 'Content-type: text/plain'
    print
    print 'You must be in the %s group to upload.' % PACKAGER_GROUP
    sys.exit(0)

print 'Content-Type: text/plain'
print

assert os.environ['REQUEST_URI'].split('/')[1] == 'repo'

form = cgi.FieldStorage()
name = check_form(form, 'name')
md5sum = check_form(form, 'md5sum')

action = None
upload_file = None
filename = None

# Is this a submission or a test?
# in a test, we don't get a file, just a filename.
# In a submission, we don;t get a filename, just the file.
if form.has_key('filename'):
    action = 'check'
    filename = check_form('filename')   
    filename = os.path.basename(filename)
    print >> sys.stderr, 'Checking file status: NAME=%s FILENAME=%s MD5SUM=%s' % (name, filename, md5sum)
else:
    action = 'upload'
    if form.has_key('file'):
        upload_file = form['file']
        if not upload_file.file:
            send_error('No file given for upload. Aborting.')
        try:
            filename = os.path.basename(upload_file.filename)
        except:
            send_error('Could not extract the filename for upload. Aborting.')
    else:
        send_error('Required field "file" is not present.')
    print >> sys.stderr, 'Processing upload request: NAME=%s FILENAME=%s MD5SUM=%s' % (name, filename, md5sum)

module_dir = os.path.join(CACHE_DIR, name)
file_dir = os.path.join(module_dir, filename)
md5_dir =  os.path.join(file_dir, md5sum)

# first test if the module really exists
cvs_dir = os.path.join(CVSREPO, name)
if not os.path.isdir(cvs_dir):
    print >> sys.stderr, 'Unknown module: %s' % name
    print 'Module "%s" does not exist!' % name
    sys.exit(-9)
    
# try to see if we already have this file...
dest_file = os.path.join(md5_dir, filename)
if os.path.exists(dest_file):
    if action == 'check':
        print 'Available'
    else:
        upload_file.file.close()
        dest_file_stat = os.stat(dest_file)
        print 'File %s already exists' % filename
        print 'File: %s Size: %d' % (dest_file, dest_file_stat.st_size)
    sys.exit(0)
elif action == 'check':
    print 'Missing'
    sys.exit(-9)

# check that all directories are in place
if not os.path.isdir(module_dir):
    os.makedirs(module_dir, 02775)

# grab a temporary filename and dump our file in there
tempfile.tempdir = my_moddir
tmpfile = tempfile.mktemp(md5sum)
tmpfd = open(tmpfile, 'w')

# now read the whole file in
m = md5_constructor()
filesize = 0
while s = upload_file.file.read(BUFFER_SIZE):
    if not s:
    	break
    tmpfd.write(s)
    m.update(s)
    filesize += len(s)

# now we're done reading, check the MD5 sum of what we got
tmpfd.close()
check_md5sum = m.hexdigest()
if md5sum != check_md5sum
    send_error("MD5 check failed. Received %s instead of %s." % (check_md5sum, md5sum))

# wow, even the MD5SUM matches. make sure full path is valid now
if not os.path.isdir(md5_dir):
    os.mkdirs(md5_dir, 02775)
    print >> sys.stderr, 'mkdir %s' % md5_dir

os.rename(tmpfile, dest_file)
print >> sys.stderr, 'Stored %s (%d bytes)' % (dest_file, filesize)
print 'File %s size %d MD5 %s stored OK' % (filename, filesize, md5sum)

