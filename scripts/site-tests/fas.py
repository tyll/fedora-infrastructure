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
                  default = 'https://admin.fedoraproject.org/accounts/login',
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
print "Starting tests on FAS"
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

print 'Testing Links:'
link_list = ['Home', 'My Account', 'New Group', 'Group List', 'Join a Group', 'About']
for link in link_list:
    print '\t %s:' % link,
    try:
      r = b.follow_link(text_regex=r'^%s$' % link)
    except LinkNotFoundError:
      print FAILED
    print OK
    headers.check(r._headers, 3000000)

print 'Editing Account:'
r = b.follow_link(text_regex=r'^My Account$')
r = b.follow_link(text_regex=r'edit')
headers.check(r._headers, 3000000)
b.select_form(nr=1)
print '\tHuman Name: %s' % b['human_name']
print '\temail: %s' % b['email']
print '\tTelephone: %s' % b['telephone']
print '\tComments: %s' % b['comments']
old_comments = b['comments']
print '\tChanging Comments Field',
b['comments'] = 'Changing for FAS test by %s' % username
r = b.submit()
print OK
headers.check(r._headers, 4000000)
r = b.follow_link(text_regex=r'edit')
headers.check(r._headers, 3000000)
print '\tVerifying comments field:',
b.select_form(nr=1)
if b['comments'] == 'Changing for FAS test by %s' % username:
  print OK
else:
  print '%s - Old comment was: %s' % (FAILED - old_comments)
r = b.submit()
headers.check(r._headers, 3000000)
print '\tResetting comments field to old value:',
r = b.follow_link(text_regex=r'edit')
b.select_form(nr=1)
b['comments'] = old_comments
r = b.submit()
print OK
headers.check(r._headers, 4000000)
print "\t**This should have generated an email to you.  Please verify that"