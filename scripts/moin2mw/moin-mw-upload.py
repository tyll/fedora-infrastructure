#!/usr/bin/python -tt

# written by seth vidal
# Altered by Mike McGrath
import mechanize
import sys
import os

# Run this from the data/pages directory in your moin install!

print "Logging in"
b = mechanize.Browser(factory=mechanize.DefaultFactory(i_want_broken_xhtml_support=True))
b.set_handle_robots(False)
b.open("https://publictest2.fedoraproject.org/wiki/Special:Userlogin")
b.select_form(nr=1)
b["wpName"] = "admin"
b["wpPassword"] = "adminadmin"
b.submit()
print "win!"
print

def upload(source, dest):
    b.open("https://publictest2.fedoraproject.org/wiki/Special:Upload")
    b.select_form(nr=1)
    b["wpDestFile"] = dest
    b['wpUploadDescription'] = 'Migrated from previous wiki'
    b['wpIgnoreWarning'] = ['true']
    b.form.add_file(open(source), filename=source)
    b.submit()
    r = b.response()
    results='\n'.join(r.readlines())
    if results.find('Success') != -1 or results.find('Migrated from previous wiki') != -1:
        print "%s - Success (%s)" % (source, dest)
    else:
        f = open('/var/tmp/%s.html' % dest, 'w')
        f.write(results)
        f.close()
        print "%s - Failure" % source

for root, directories, files in os.walk('./'):
    for file in [f for f in files]:
        target = root + '/' + file
        if target.find('attachment') != -1 and os.path.isfile(target):
            dest = target
            dest = dest.replace('./', '', 1)
            dest = dest.replace('/attachments', '', 1)
            dest = dest.replace('(2f)', '_')
            dest = dest.replace('/', '_')
            upload(target, dest)
            

sys.exit()

#r = b.response()


