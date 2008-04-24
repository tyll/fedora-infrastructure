#!/usr/bin/python

#!/usr/bin/python2

import sys, os, errno
import website, crypt
import getopt, re

GRANT_DIRECT = 0
GRANT_DERIVED = 1
GRANT_REGEXP = 2

DRY_RUN = False

def get_bz_user_id(bzdbh, username):
    bzdbc = bzdbh.cursor()
    bzdbc.execute("SELECT userid FROM profiles WHERE login_name = %s",
            (username.lower(),))
    if bzdbc.rowcount:
        return bzdbc.fetchone()[0]

opts, args = getopt.getopt(sys.argv[1:], '', ('usage', 'help'))
if len(args) < 1 or ('--usage','') in opts or ('--help','') in opts:
    print """
Usage: bz-make-components.py FILENAME...
"""
    sys.exit(1)

bzdbh = website.get_dbh('bugs', 'bugs')
bzdbc = bzdbh.cursor()

bzdbh.commit()
need_emails = {}
for curfile in args:
    if not os.path.exists(curfile):
        continue
    fh = open(curfile, 'r')
    lnum = 0
    while 1:
        aline = fh.readline()
        lnum += 1
        if not aline:
            break
        aline = aline.strip()
        if not aline or aline[0] == '#':
            continue

        pieces = aline.split('|')
        try:
            product, component, description, owner, qa = pieces[:5]
        except:
            print "Invalid line %s at %s:%s" % (aline, curfile, lnum)
        cclist = []
        owners = owner.split(',')
        owner = owners[0]
        if len(owners) > 1:
            for I in owners[1:]:
                Inum = get_bz_user_id(bzdbh, I)
                if Inum is None:
                    if not need_emails.has_key(I):
                        need_emails[I] = []
                    need_emails[I].append((product, component, curfile, lnum))
                    continue
                cclist.append(Inum)
        owner_num = get_bz_user_id(bzdbh, owner)
        qa_num = get_bz_user_id(bzdbh, qa)
        if owner_num is None:
            if not need_emails.has_key(owner):
                need_emails[owner] = []
            need_emails[owner].append((product, component, curfile, lnum))
#            print "Invalid owner %s at %s:%s" % (owner, curfile, lnum)
            continue
        if len(pieces) > 5 and pieces[5]:
            for I in pieces[5].split(','):
                Inum = get_bz_user_id(bzdbh, I)
                if Inum is None:
                    if not need_emails.has_key(I):
                        need_emails[I] = []
                    need_emails[I].append((product, component, curfile, lnum))
                    continue
                cclist.append(Inum)

        if product != "Fedora" and product[:len('Fedora ')] != 'Fedora ':
            print "Invalid product %s at %s:%s" % (product, curfile, lnum)
            continue

        bzdbc.execute("SELECT id FROM products WHERE name = %s", (product,))
        if not bzdbc.rowcount:
            if DRY_RUN:
                print "Need to create product %s" %(product,)
                sys.exit(0)
            else:
                bzdbc.execute("INSERT INTO products (name, description, disallownew, votesperuser, maxvotesperbug, votestoconfirm, defaultmilestone, depends) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (product, product, 0, 0, 10000, 0, '---', 0))
                bzdbc.execute("SELECT id FROM products WHERE name = %s", (product,))
                product_id = bzdbc.fetchone()[0]
                bzdbc.execute("INSERT INTO versions (value, product_id) VALUES (%s, %s)", ("development", product_id))
                bzdbc.execute("INSERT INTO milestones (product_id, value, sortkey) VALUES (%s, '---', 0)", (product_id,))
        else:
            product_id = bzdbc.fetchone()[0]

        bzdbc.execute("SELECT * FROM components WHERE product_id = %s AND name = %s", (product_id, component))
        if bzdbc.rowcount:
            arow = bzdbc.fetchhash()
            if DRY_RUN:
                print("component update of %s:  UPDATE components SET initialowner = %s, initialqacontact = %s, initialcclist = %s WHERE id = %s",
                              (component, owner_num, qa_num, ':'.join(map(str,cclist)), arow['id']))
            else:
                bzdbc.execute("UPDATE components SET initialowner = %s, initialqacontact = %s, initialcclist = %s WHERE id = %s",
                          (owner_num, qa_num, ':'.join(map(str,cclist)), arow['id']))
        else:
            if DRY_RUN:
                print("create component: INSERT INTO components (name, product_id, description, initialowner, initialqacontact, initialcclist) VALUES (%s, %s, %s, %s, %s, %s)",
                          (component, product_id, description, owner_num, qa_num, ':'.join(map(str,cclist))))
            else:
                bzdbc.execute("INSERT INTO components (name, product_id, description, initialowner, initialqacontact, initialcclist) VALUES (%s, %s, %s, %s, %s, %s)",
                          (component, product_id, description, owner_num, qa_num, ':'.join(map(str,cclist))))
bzdbh.commit()

for I, J in need_emails.items():
    if not I.strip():
        print "Need an e-mail for", J
        continue
    print "Sending e-mail to", I
    if DRY_RUN:
        continue
    website.send_email("accounts@fedora.redhat.com", I, "You need to create a bugzilla account for %s" % I, """
In order to make bugzilla components for Fedora-related programs, we need to have an existing bugzilla account for 
the listed owner. You (%s) do not have a bugzilla account, but are listed as the owner for the following components:
%s

Please create a bugzilla account for %s immediately, because this amazingly stupid cron job will keep sending you an 
e-mail every hour until you do :)

- The management
""" % (I, '\n'.join(map(lambda x: "%s (%s)" % x[:2], J)), I))
