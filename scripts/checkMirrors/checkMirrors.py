#! /usr/bin/env python
#
# [Author]
# Davi Vercillo C. Garcia (davivercillo@gmail.com)
# 
# [License]
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

import sys
import urllib
from signal import signal, SIG_DFL

signal(2, SIG_DFL)

if len(sys.argv) < 4:
    print "Use: ./mirror_checker.py updates 11 x86_64"
    sys.exit(-1)

main_mirror = "http://download.fedora.redhat.com/pub/fedora/linux/%s/%s/%s/repodata/"
mirror_list = "http://mirrors.fedoraproject.org/mirrorlist?path=/pub/fedora/linux/%s/%s/%s/repodata&country=global"
xml_file = "repomd.xml"

directory = sys.argv[1]
version = sys.argv[2]
architecture = sys.argv[3]

try:
    mirrors = urllib.urlopen(mirror_list % (directory, version, architecture)).read().split("\n")
    repomd = urllib.urlopen(main_mirror % (directory, version, architecture) + xml_file).read()
except Exception, err:
    print "[ERROR] Cannot get info from URLs. Please check the parameters."
    sys.exit(-1)

num_total = len(mirrors)
num_good = 0
num_bad = 0
num_error = 0
results = [[],[], []]

print "\nChecking the repositories repodata !\n\nUsing:", main_mirror % (directory, version, architecture)

for url in mirrors:
    if "#" in url or not url:
        continue
    print "\rTesting: %d/%d" % (num_good, num_total),
    sys.stdout.flush()
    try:
        if urllib.urlopen(url + xml_file).read() == repomd:
            results[0].append(url)
            num_good += 1
        else:
            results[1].append(url)
            num_bad += 1
    except Exception, err:
        results[2].append(url)
        num_error += 1

print """\n
========================== Results ==========================
\tGood\tBad\tError\tTotal\tPerc.Good
\t%4d\t%3d\t%5d\t%5d\t%7.2f%%
=============================================================

[Good Repositories]
%s

[Bad Repositories]
%s

[Errors]
%s
""" % (num_good, num_bad, num_error, num_total , float(num_good)*100/(num_good + num_bad),
       "\n".join(results[0]),
       "\n".join(results[1]),
       "\n".join(results[2]),)

sys.exit(0)

