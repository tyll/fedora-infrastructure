#!/usr/bin/python -tt

import yum
import sys
from operator import attrgetter
from fedora.client.pkgdb import PackageDB

pkgdb = PackageDB()

bugzacl = pkgdb.get_bugzilla_acls()

my = yum.YumBase()
my.preconf.root ='/var/tmp/skvidal-chroot'
my.preconf.debuglevel=0
my.arch.archlist.append('src')
my.setCacheDir()
my.repos.disableRepo('*')
my.add_enable_repo('f14',
   baseurls=['http://download.fedora.redhat.com/pub/fedora/linux/development/14/source/SRPMS/'])
my.add_enable_repo('f14-updates',
   baseurls=['http://download.fedora.redhat.com/pub/fedora/linux/updates/testing/14/SRPMS/'])   
#my.add_enable_repo('f14-updates',
#   baseurls=['http://download.fedora.redhat.com/pub/fedora/linux/updates/14/SRPMS/',
#            'http://download.fedora.redhat.com/pub/fedora/linux/updates/testing/14/SRPMS/'])
my.add_enable_repo('f13', 
   baseurls=['http://fedora.mirrors.tds.net/pub/fedora/releases/13/Everything/source/SRPMS/'])
my.add_enable_repo('f13-updates', 
   baseurls=['http://fedora.mirrors.tds.net/pub/fedora/updates/13/SRPMS/',
              'http://download.fedora.redhat.com/pub/fedora/linux/updates/testing/13/SRPMS/'])

len(my.pkgSack) # just to frob the sack

f14repo = my.repos.findRepos('f14')[0]
f14updates = my.repos.findRepos('f14-updates')[0]

def whoowns(package):
    """<package>

    Retrieve the owner of a given package
    """
    try:
        mainowner = bugzacl['Fedora'][package]['owner']
    except KeyError:
        irc.reply("No such package exists.")
        return
    others = []
    for key in bugzacl.keys():
        if key == 'Fedora':
            continue
        try:
            owner = bugzacl[key][package]['owner']
            if owner == mainowner:
                continue
        except KeyError:
            continue
        others.append("%s in %s" % (owner, key))
    return mainowner


owners = []
for pkg in sorted(my.pkgSack.returnNewestByNameArch()):
    if not pkg.repoid.startswith('f14'):
        f14pkgs = []
        f14upkgs = []
        f14all = []
        try:
            f14pkgs = f14repo.sack.returnNewestByNameArch((pkg.name, pkg.arch))
            f14upkgs = f14updates.sack.returnNewestByNameArch((pkg.name, pkg.arch))
        except yum.Errors.PackageSackError, e:
            pass
        f14all.extend(f14upkgs)
        f14all.extend(f14pkgs)
        if f14all:
            f14all.sort()
            f14all.reverse()
            if f14all[0].EVR != pkg.EVR:
                owner = whoowns(pkg.name)
                owners.append(owner)
                print 'greater for f13: %s (%s)' % (pkg.name, owner)
                print ' f13 = %s' % pkg
                print ' f14 = %s' % f14all[0]

print '%s@fedoraproject.org' % '@fedoraproject.org,'.join(sorted(set(owners)))
