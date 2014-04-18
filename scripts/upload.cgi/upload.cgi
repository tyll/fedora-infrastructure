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
import pwd
import syslog
import smtplib

from email import Header, Utils
try:
    from email.mime.text import MIMEText
except ImportError:
    from email.MIMEText import MIMEText

import hashlib

# Reading buffer size
BUFFER_SIZE = 4096

# We check modules exist from this dircetory
CVSREPO = '/cvs/pkgs/rpms'

# Lookaside cache directory
CACHE_DIR = '/srv/cache/lookaside/pkgs'

# Fedora Packager Group
PACKAGER_GROUP = 'packager'

def send_error(text):
    print text
    sys.exit(1)

def check_form(form, var):
    ret = form.getvalue(var, None)
    if ret is None:
        send_error('Required field "%s" is not present.' % var)
    if isinstance(ret, list):
        send_error('Multiple values given for "%s". Aborting.' % var)
    return ret

def check_auth(username):
    authenticated = False
    try:
        if username in grp.getgrnam(PACKAGER_GROUP)[3]:
            authenticated = True
    except KeyError:
        pass
    return authenticated

def send_email(pkg, checksum, filename, username):
    text = """A file has been added to the lookaside cache for %(pkg)s:

%(checksum)s  %(filename)s""" % locals()
    msg = MIMEText(text)
    try:
        sender_name = pwd.getpwnam(username)[4]
        sender_email = '%s@fedoraproject.org' % username
    except KeyError:
        sender_name = ''
        sender_email = 'nobody@fedoraproject.org'
        syslog.syslog('Unable to find account info for %s (uploading %s)' %
                      (username, filename))
    if sender_name:
        try:
            sender_name = unicode(sender_name, 'ascii')
        except UnicodeDecodeError:
            sender_name = Header.Header(sender_name, 'utf-8').encode()
            msg.set_charset('utf-8')
    sender = Utils.formataddr((sender_name, sender_email))
    recipients = ['%s-owner@fedoraproject.org' % pkg,
                  'fedora-extras-commits@redhat.com']
    msg['Subject'] = 'File %s uploaded to lookaside cache by %s' % (
            filename, username)
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['X-Fedora-Upload'] = '%s, %s' % (pkg, filename)
    try:
        s = smtplib.SMTP('bastion')
        s.sendmail(sender, recipients, msg.as_string())
    except:
        syslog.syslog('sending mail for upload of %s failed!' % filename)

def main():
    os.umask(002)

    username = os.environ.get('SSL_CLIENT_S_DN_CN', None)
    if not check_auth(username):
        print 'Status: 403 Forbidden'
        print 'Content-type: text/plain'
        print
        print 'You must connect with a valid certificate and be in the %s group to upload.' % PACKAGER_GROUP
        sys.exit(0)

    print 'Content-Type: text/plain'
    print

    assert os.environ['REQUEST_URI'].split('/')[1] == 'repo'

    form = cgi.FieldStorage()
    name = check_form(form, 'name')

    # Search for the file hash, start with stronger hash functions
    if form.has_key('sha512sum'):
        checksum = check_form(form, 'sha512sum')
        hash_type = "sha512"

    elif form.has_key('md5sum'):
        # Fallback on md5, as it's what we currently use
        checksum = check_form(form, 'md5sum')
        hash_type = "md5"

    else:
        send_error('Required checksum is not present.')

    action = None
    upload_file = None
    filename = None

    # Is this a submission or a test?
    # in a test, we don't get a file, just a filename.
    # In a submission, we don;t get a filename, just the file.
    if form.has_key('filename'):
        action = 'check'
        filename = check_form(form, 'filename')
        filename = os.path.basename(filename)
        print >> sys.stderr, '[username=%s] Checking file status: NAME=%s FILENAME=%s %sSUM=%s' % (username, name, filename, hash_type.upper(), checksum)
    else:
        action = 'upload'
        if form.has_key('file'):
            upload_file = form['file']
            if not upload_file.file:
                send_error('No file given for upload. Aborting.')
            filename = os.path.basename(upload_file.filename)
        else:
            send_error('Required field "file" is not present.')
        print >> sys.stderr, '[username=%s] Processing upload request: NAME=%s FILENAME=%s %sSUM=%s' % (username, name, filename, hash_type.upper(), checksum)

    module_dir = os.path.join(CACHE_DIR, name)
    hash_dir = os.path.join(module_dir, filename, hash_type, checksum)

    if hash_type == "md5":
        # Preserve compatibility with the current folder hierarchy for md5
        hash_dir =  os.path.join(module_dir, filename, checksum)

    # first test if the module really exists
    cvs_dir = os.path.join(CVSREPO, name)
    if not os.path.isdir(cvs_dir):
        print >> sys.stderr, '[username=%s] Unknown module: %s' % (username, name)
        send_error('Module "%s" does not exist!' % name)

    # try to see if we already have this file...
    dest_file = os.path.join(hash_dir, filename)
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
        sys.exit(0)

    # check that all directories are in place
    if not os.path.isdir(module_dir):
        os.makedirs(module_dir, 02775)

    # grab a temporary filename and dump our file in there
    tempfile.tempdir = module_dir
    tmpfile = tempfile.mkstemp(checksum)[1]
    tmpfd = open(tmpfile, 'w')

    # now read the whole file in
    m = getattr(hashlib, hash_type)()
    filesize = 0
    while True:
        data = upload_file.file.read(BUFFER_SIZE)
        if not data:
            break
        tmpfd.write(data)
        m.update(data)
        filesize += len(data)

    # now we're done reading, check the checksum of what we got
    tmpfd.close()
    check_checksum = m.hexdigest()
    if checksum != check_checksum:
        os.unlink(tmpfile)
        send_error("MD5 check failed. Received %s instead of %s." % (check_checksum, checksum))

    # wow, even the checksum matches. make sure full path is valid now
    if not os.path.isdir(hash_dir):
        os.makedirs(hash_dir, 02775)
        print >> sys.stderr, '[username=%s] mkdir %s' % (username, hash_dir)

    os.rename(tmpfile, dest_file)
    os.chmod(dest_file, 0644)

    print >> sys.stderr, '[username=%s] Stored %s (%d bytes)' % (username, dest_file, filesize)
    print 'File %s size %d %s %s stored OK' % (filename, filesize, hash_type.upper(), checksum)
    send_email(name, checksum, filename, username)

if __name__ == '__main__':
    main()
