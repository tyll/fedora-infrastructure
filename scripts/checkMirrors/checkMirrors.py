#! /usr/bin/env python
# coding: utf-8
#
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

__AUTHOR__ = "Davi Vercillo C. Garcia (davivercillo@gmail.com)"
__VERSION__ = "0.2"
__DATE__ = "21/07/2009"

import sys
import urllib2
from signal import signal, SIG_DFL

class CheckMirrors:
    """Class that check repodata on the mirrors.
    """
    def __init__(self, directory, version, architecture):
        """Class constructor.
        directory -> (String) Ex: updates
        version -> : (String) Ex: 11
        architecture -> (String) Ex: x86_64
        """
        if type(directory) != str or type(version) != str or type(architecture) != str:
            raise TypeError, "Parameters need to be strings."
        self.mirror_list_url = "http://mirrors.fedoraproject.org/mirrorlist?path=/pub/fedora/linux/%s/%s/%s/repodata&country=global"
        self.main_mirror = "http://download.fedora.redhat.com/pub/fedora/linux/%s/%s/%s/repodata/"
        self.xml_filename = "repomd.xml"
        self.directory = directory
        self.version = version
        self.architecture = architecture
        self.number_total_mirrors = 0
        self.good_mirrors = [[], 0]
        self.bad_mirrors = [[], 0]
        self.error_mirrors = [[], 0]
    
    def get_mirror_list(self):
        """Method that connect on fedoraproject.org, get the mirror list and the repomd.xml.
        """
        temp = self.mirror_list_url % (self.directory, self.version, self.architecture)
        try:
            self.mirrors = [ url
                             for url in urllib2.urlopen(temp).read().split("\n")
                             if url != "" and not "#" in url ]
        except Exception, error:
            print "[ERROR] Failed to get mirror list:", error
            sys.exit(-1)
        temp = self.main_mirror % (self.directory, self.version, self.architecture)
        try:
            print temp + self.xml_filename
            self.repodata = urllib2.urlopen(temp + self.xml_filename).read()
        except Exception, error:
            print "[ERROR] Failed to get XML repodata file:", error
            sys.exit(-1)
        self.number_total_mirrors = len(self.mirrors)
        if self.number_total_mirrors == 0:
            print "[ERROR] Did you specify the right options ?"
            sys.exit(-1)
    
    def check_mirrors(self):
        """Method that verify, for each mirror, if its repomd.xml is equal of that on main.
        """
        print "\nChecking the repositories repodata !\n\nUsing:", self.main_mirror % (self.directory, self.version, self.architecture)            
        for url in self.mirrors:
            print "\rTesting: %d/%d" % (self.good_mirrors[1] , self.number_total_mirrors),
            sys.stdout.flush()
            try:
                if urllib2.urlopen(url + self.xml_filename, timeout=10).read() == self.repodata:
                    self.good_mirrors[0].append(url)
                    self.good_mirrors[1] += 1
                else:
                    self.bad_mirrors[0].append(url)
                    self.bad_mirrors[1] += 1
            except Exception, error:
                self.error_mirrors[0].append(url + "\n[" + str(error) + "]")
                self.error_mirrors[1] += 1
    
    def print_results(self):
        """Method that put the results on STDOUT.
        """
        print """\n
=============== Valid Mirror Results ========================
\tGood\tBad\tError\tTotal\tPerc.Good
\t%4d\t%3d\t%5d\t%5d\t%7.2f%%
=============================================================

[Good Repositories]
%s

[Bad Repositories]
%s

[Errors]
%s
""" % (self.good_mirrors[1],
       self.bad_mirrors[1],
       self.error_mirrors[1],
       self.number_total_mirrors,
       float(self.good_mirrors[1])*100/self.number_total_mirrors,
       "\n".join(self.good_mirrors[0]),
       "\n".join(self.bad_mirrors[0]),
       "\n".join(self.error_mirrors[0]),)
    
    def run(self):
        """Method that execute all method in the right order.
        """
        self.get_mirror_list()
        self.check_mirrors()
        self.print_results()
    

if __name__ == "__main__":
    """Main Function.
    If the programs was called as a script, this will be executed.
    """
    signal(2, SIG_DFL)
    if len(sys.argv) == 4:
        CheckMirrors(sys.argv[1], sys.argv[2], sys.argv[3], ).run()
        sys.exit(0)
    else:
        print "[ERROR] Use: ./mirror_checker.py <directory> <version> <architecture>"
        sys.exit(-1)
    
