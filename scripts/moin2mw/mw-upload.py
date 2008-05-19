#!/usr/bin/python -tt

# written by seth vidal
# Altered by Mike McGrath
import mechanize
import sys

try:
    sys.argv[2]
except IndexError:
    print "Please specify [source] [dest name]"
    sys.exit()
try:
    sys.argv[3]
except IndexError:
    pass
else:
    print "Please specify [source] [dest name]"
    sys.exit()

try:
    f = open(sys.argv[1])
except IOError:
    print "Could not open %s" % sys.argv[1]
    sys.exit()

b = mechanize.Browser(factory=mechanize.DefaultFactory(i_want_broken_xhtml_support=True))
b.set_handle_robots(False)
b.open("https://publictest1.fedoraproject.org/wiki/Special:Userlogin")
b.select_form(nr=1)
b["wpName"] = "admin"
b["wpPassword"] = "adminadmin"
b.submit()
r = b.response()

b.open("https://publictest1.fedoraproject.org/wiki/Special:Upload")
b.select_form(nr=1)
b["wpDestFile"] = sys.argv[2]
b['wpUploadDescription'] = 'Migrated from previous wiki'
b.form.add_file(open(sys.argv[1]), filename=sys.argv[1])
b.submit()
r = b.response()
results='\n'.join(r.readlines())
if results.find('Success') != -1 or results.find('Migrated from previous wiki') != -1:
    print "%s - Success" % sys.argv[1]
else:
    print "%s - Failure" % sys.argv[1]
