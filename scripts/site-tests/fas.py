#!/usr/bin/python
# -*- coding: utf-8 -*-

import getpass
import mechanize
import sys

from optparse import OptionParser
from mechanize import Browser, LinkNotFoundError
from urllib import urlencode
from urllib2 import HTTPError
from tests import *

parser = OptionParser()

parser.add_option('-u', '--username',
                  dest = 'username',
                  default = getpass.getuser(),
                  metavar = 'username',
                  help = 'Username to connect with (default: %default)')
parser.add_option('-p', '--password',
                  dest = 'password',
                  default = None,
                  metavar = 'password',
                  help = 'Password to connect with (Will prompt if not specified')
parser.add_option('-b', '--baseurl',
                  dest = 'baseurl',
                  default = 'https://admin.fedoraproject.org/accounts/',
                  metavar = 'baseurl',
                  help = 'Url to fas (default: %default)')
parser.add_option('-d', '--debug',
                  dest = 'debug',
                  default = False,
                  action = 'store_true',
                  help = 'Url (default: False)')
(opts, args) = parser.parse_args()

username = opts.username
headers = Headers(debug=opts.debug)

if not opts.password:
  password = getpass.getpass('FAS password for %s: ' % username)
else:
  password = opts.password
del getpass

print
print
print "Starting tests on MirrorManager"
print "         Note: Results shown in terms of test success.  Anything not OK should be looked at"
print

b = Browser()
b.set_handle_robots(False)
data = urlencode({'user_name': username,
                  'password': password,
                  'login': 'Login'})
data_bad = urlencode({'user_name': username,
                  'password': 'badpass',
                  'login': 'Login'})


print 'Logging in bad password:',
try:
  r = b.open(opts.baseurl, data=data_bad)
except HTTPError, e:
  print OK
else:
  print FAILED

print 'Logging in good password:',
try:
  r = b.open(opts.baseurl, data=data)
except HTTPError, e:
  print '%s - %s' % (FAILED, e)
else:
  print OK
headers.check(r._headers, 3000000)

