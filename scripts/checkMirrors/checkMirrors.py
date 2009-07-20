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

results = [[],[]]
for url in mirrors:
    if "#" in url or not url:
        continue
    print ".",
    sys.stdout.flush()
    try:
        if urllib.urlopen(url + xml_file).read() == repomd:
            results[0].append(url)
        else:
            results[1].append(url)
    except Exception, err:
        print "[ERROR]", url

print "\nUsing:", main_mirror % (directory, version, architecture), "\n"
print "[Good]"
for url in results[0]:
    print url
print "\n[Bad]"
for url in results[1]:
    print url

print "\n"
sys.exit(0)

