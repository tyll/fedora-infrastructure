#!/usr/bin/python -tt

import yum
import sys
from operator import attrgetter

my = yum.YumBase()
my.preconf.root ='/var/tmp/skvidal-chroot'
my.preconf.debuglevel=0
my.arch.archlist.append('src')
my.setCacheDir()
my.repos.disableRepo('*')
my.add_enable_repo('f13',
   baseurls=['http://fedora.mirrors.tds.net/pub/fedora/development/13/source/SRPMS/'])
my.add_enable_repo('f12', 
   baseurls=['http://fedora.mirrors.tds.net/pub/fedora/releases/12/Everything/source/SRPMS/'])
my.add_enable_repo('f12-updates', 
   baseurls=['http://fedora.mirrors.tds.net/pub/fedora/updates/12/SRPMS/'])

len(my.pkgSack) # just to frob the sack

f13repo = my.repos.findRepos('f13')[0]

for pkg in my.pkgSack.returnNewestByNameArch():
    if pkg.repoid != 'f13':
        try:
            f13pkgs = f13repo.sack.returnNewestByNameArch((pkg.name, pkg.arch))
        except yum.Errors.PackageSackError, e:
            f13pkgs = []

        if f13pkgs:
            if f13pkgs[0].EVR != pkg.EVR:
                print 'greater for f12: %s' % pkg.name
                print ' f12 = %s' % pkg
                print ' f13 = %s' % f13pkgs[0]
        else:
            print 'not in f13 at all: %s' % pkg.name
