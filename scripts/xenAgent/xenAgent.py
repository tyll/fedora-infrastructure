#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright © 2008 Red Hat, Inc. All rights reserved.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author: Mike McGrath <mmcgrath@redhat.com>
#

# Sample Use:
# See what guests are running:
# 
# snmpwalk -v2c -c public localhost .1.3.6.1.4.1.2021.1.1
#
# Reboot a guest (requres rw access and rw password):
#
# snmpset -v2c -c private localhost .1.3.6.1.4.1.2021.1.1.1 s reboot
# 
# Sample use (add to /etc/snmp/snmpd.conf)
#
# pass .1.3.6.1.4.1.2021.1 /usr/bin/python /path/to/xenAgent.py

import sys
import commands
from optparse import OptionParser

BASE='.1.3.6.1.4.1.2021.1'

# BASE.1.1 == First running xen guest
# BASE.1.2 == Second running xen guest, etc
# BASE.2 == Free memory on dom0

parser = OptionParser(version = '1.0')

parser.add_option('-s', '--set',
                  dest = 'set',
                  default = False,
                  metavar = 'set',
                  help = 'Set a value')
parser.add_option('-g', '--get',
                  dest = 'get',
                  default = False,
                  metavar = 'get',
                  help = 'Get a value')
parser.add_option('-n', '--next',
                  dest = 'get_next',
                  default = False,
                  metavar = 'get_next',
                  help = 'Get next oid in the tree')

def getRunning():
    ''' Return a list of running hosts'''
    # This is in place because the libvirt and xen apis are not working right
    # on our xen hosts.
    running_raw=commands.getoutput('/usr/sbin/xm list').split('\n')[2:]
    running = []
    for line in running_raw:
        if line.strip():
            running.append(line.split(' ')[0].strip())
    return running

(opts, args) = parser.parse_args()


# Set a value
if opts.set:
    set = opts.set
    if set.startswith('%s.1.' % BASE):
        running = getRunning()
        command = ' '.join(sys.argv[4:])
        cur_host = int(set.replace('%s.1.' % BASE, ''))
        if command == 'reboot':
            # So the question here is, do we do a reboot (similar to ctl + alt + del)
            # or do we a destroy followed by a create?  The first one is much safer but
            # might not work all the time.  We'll start there though
            commands.getoutput('/usr/sbin/xm reboot %s' % running[cur_host]).split('\n')[2:]
    sys.exit(0)


# Take an OID, print the next OID in the sequence
# Used for snmpwalks
if opts.get_next:
    get_next = opts.get_next
    next = ''
    if get_next == BASE:
        running = getRunning()
        if running >= 1:
            next = "%s.1.0" % BASE
        else:
            next = "%s.2" % BASE
    elif get_next == '%s.1' % BASE:
        next = '%s.1.0' % BASE
    elif get_next.startswith('%s.1.' % BASE):
        cur_host = get_next.replace('%s.1.' % BASE, '')
        running = getRunning()
        if len(running) > int(cur_host) + 1:
            next = "%s.1.%s" % (BASE, int(cur_host) + 1)
        else:
            next = "%s.2" % BASE
    else:
        sys.exit(0)
else:
    next = opts.get

print next

# Get the value of an OID
if opts.get or opts.get_next:
    get = next
    if get == '%s' % BASE:
        print "string"
        print "This is a xen host"
        sys.exit(0)
    if get.startswith('%s.1.' % BASE):
        running = getRunning()
        host = int(get.replace('%s.1.' % BASE, ''))
        print "string"
        print running[host]
        sys.exit(0)
    if get == '%s.2' % BASE:
        print "string"
        print "not implemented"
        sys.exit(0)
    print "string"
    print "ack... %s %s" % (next, get)
