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
my.add_enable_repo('f13-updates',
   baseurls=['http://download.fedora.redhat.com/pub/fedora/linux/updates/testing/13/SRPMS/'])   
my.add_enable_repo('f12', 
   baseurls=['http://fedora.mirrors.tds.net/pub/fedora/releases/12/Everything/source/SRPMS/'])
my.add_enable_repo('f12-updates', 
   baseurls=['http://fedora.mirrors.tds.net/pub/fedora/updates/12/SRPMS/'])

len(my.pkgSack) # just to frob the sack

f13repo = my.repos.findRepos('f13')[0]
f13updates = my.repos.findRepos('f13-updates')[0]

for pkg in sorted(my.pkgSack.returnNewestByNameArch()):
    if not pkg.repoid.startswith('f13'):
        f13pkgs = []
        f13upkgs = []
        f13all = []
        try:
            f13pkgs = f13repo.sack.returnNewestByNameArch((pkg.name, pkg.arch))
            f13upkgs = f13updates.sack.returnNewestByNameArch((pkg.name, pkg.arch))
        except yum.Errors.PackageSackError, e:
            pass
        f13all.extend(f13upkgs)
        f13all.extend(f13pkgs)
        if f13all:
            f13all.sort()
            f13all.reverse()
            if f13all[0].EVR != pkg.EVR:
                print 'greater for f12: %s' % pkg.name
                print ' f12 = %s' % pkg
                print ' f13 = %s' % f13all[0]
