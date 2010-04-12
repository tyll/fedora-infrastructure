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
                  default = 'https://admin.fedoraproject.org/mirrormanager/',
                  metavar = 'baseurl',
                  help = 'Url to mirrormanager (default: %default)')
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

print 'Getting Link Count:',
hosts = sites = 0
l = b.links()
try:
  while 1:
    link = l.next()
    if link.url.startswith('/mirrormanager/site/'):
      sites += 1
    if link.url.startswith('/mirrormanager/host/'):
      hosts += 1
except StopIteration:
  pass
print OK
print '\tHosts %s - %s' % is_normal(hosts, 580)
print '\tSites %s - %s' % is_normal(sites, 555)


print 'Creating Site:',
r = b.follow_link(text_regex=r'Add Site')
b.select_form(name='form')
b['name'] = 'Fedora Admin Test Site - %s' % username
b['password'] = 'Test'
b['orgUrl'] = 'http://fedoraproject.org/'
b['downstreamComments'] = 'This is a test site, it should not exist.  Please let admin@fedoraproject.org know it is here'
r = b.submit()
print OK

headers.check(r._headers, 3000000)

print 'Verifying Site:',
b.follow_link(text_regex=r'Main')
b.follow_link(text_regex=r'Fedora Admin Test Site - %s' % username)
b.select_form(name='form')
if b['name'] == 'Fedora Admin Test Site - %s' % username:
  print '%s - %s' % (OK, b['name'])
else:
  print '%s - %s' % (FAILED, b['name'])
  sys.exit(1)

print 'Deleting Site:',
r = b.follow_link(text_regex=r'Delete Site')
print OK
headers.check(r._headers, 3000000)

print 'Verifying Deletion:',
r = b.follow_link(text_regex=r'Main')
try:
  b.follow_link(text_regex=r'Fedora Admin Test Site - %s' % username)
except LinkNotFoundError:
  print OK
else:
  print '%s - Site still exists!  Please examine' % FAILED
headers.check(r._headers, 3000000)


print 'Verifying Public List:'
r = b.open('http://mirrors.fedoraproject.org/publiclist/')
for version in [10, 11, 'rawhide']:
    print 'Looking for %s' % version,
    print '%s - %s' % (OK, b.find_link(text_regex=r'^%s$' % version).url)
headers.check(r._headers, 3000)


print 'Verifying mirrorlist:'
print '\tgeneric test:',
r = b.open('http://mirrors.fedoraproject.org/mirrorlist?repo=fedora-11&arch=i386')
generic_count = len(r.readlines()) - 1
print '\t %s - %s' % is_normal(generic_count, 50)
headers.check(r._headers, 300000)

print '\tglobal test:',
r = b.open('http://mirrors.fedoraproject.org/mirrorlist?repo=fedora-11&arch=i386&country=global')
generic_count = len(r.readlines()) - 1
print '\t %s - %s' % is_normal(generic_count, 170)
headers.check(r._headers, 300000)

print '\tgeoipv4 test:',
r = b.open('http://mirrors.fedoraproject.org/mirrorlist?repo=fedora-11&arch=i386&ip=64.34.163.94')
if r.readline().count('country = US'):
  print OK
else:
  print FAILED
headers.check(r._headers, 300000)

print '\tgeoipv6 test:',
r = b.open('http://mirrors.fedoraproject.org/mirrorlist?repo=fedora-11&arch=i386&ip=2610:28:200:1:216:3eff:fe62:9fdd')
if r.readline().count('country = US'):
  print OK
else:
  print FAILED
headers.check(r._headers, 300000)

print '\tASN test:',
r = b.open('http://mirrors.fedoraproject.org/mirrorlist?repo=fedora-11&arch=i386&ip=64.34.163.94')
tmp = r.readline()
#if r.readline().count('Using ASN 30099') and r.readline().count('serverbeach1'):
if tmp.count('Using ASN 30099') and tmp.count('serverbeach1'):
  print OK
else:
  print FAILED
  print tmp
headers.check(r._headers, 300000)
