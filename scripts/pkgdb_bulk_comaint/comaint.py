#!/usr/bin/python -tt

import sys
import getpass

from fedora.client import PackageDB

if __name__ == '__main__':
    print 'Username: ',
    username = sys.stdin.readline().strip()
    password = getpass.getpass('Password: ')

    # Note: in order not to send email:
    # ssh bapp01
    # /usr/sbin/puppetd --disable
    # edit /etc/pkgdb.cfg and set:
    #   mail.on = False
    # /etc/init.d/httpd restart
    #
    # Then run this script on a host that can talk to bapp01.
    pkgdb = PackageDB('http://bapp01/pkgdb/', username=username, password=password)
    collections = dict([(c[0]['id'], c[0]) for c in pkgdb.get_collection_list(eol=False)])
    pkgs = pkgdb.user_packages('mmaslano', acls=['owner', 'approveacls']).pkgs

    for pkg in (p for p in pkgs if p['name'].startswith('perl-')):
        c_ids = (p['collectionid'] for p in pkg['listings'] if p['collectionid'] in collections)
        branches = [collections[c]['branchname'] for c in c_ids]
        pkgdb.edit_package(pkg['name'], comaintainers=['ppisar'], branches=branches)

    sys.exit(0)
