#!/usr/bin/env python
# XML_RPC interface to "Hosting request" tickets on fedorahosted Trac.

import sys, urllib, xmlrpclib
USERNAME = ''
PASSWORD = ''
SERVER = 'fedorahosted.org'
PROJECT_PATH = 'fedora-infrastructure'

xmlrpc = xmlrpclib.ServerProxy("https://%s:%s@%s/%s/login/xmlrpc" % (
    urllib.quote(USERNAME), urllib.quote(PASSWORD), SERVER, PROJECT_PATH))

multicall = xmlrpclib.MultiCall(xmlrpc)

def parse_line(search, shortname, line):
    global project
    if search in line:
        project[shortname] = line.split(": ", 1)[1]
    return None
    

for ticket in xmlrpc.ticket.query("summary=^Hosting request&status=new|open"):
    #print "Ticket #" + str(ticket)
    ticket_info = xmlrpc.ticket.get(ticket)
    if ticket == 2152: # Just for testing purposes, on hosted2.
        project = {}
        project['mailing_lists'] = []
        description = ticket_info[3]['description'] # For now, assume [3] will always be the dictionary.
        description = description.split("\n")
        for line in description:
            # parse_line(Search, Short-Name, line)
            parse_line("Project name: ", "name", line)
            parse_line("Project short summary", "summary", line)
            parse_line("SCM choice", "scm", line)
            parse_line("Trac instance", "trac", line)
            parse_line("mailing list", "mailinglist", line)
            
        if project['mailinglist'].lower() != "no":
            lists = project['mailinglist'].split(",")
            
            for list_name in lists:
                # Kill spaces
                list_name = list_name.replace(" ", "")
                
                # Append it to the list, so we can iterate over it later.
                project['mailing_lists'].append(list_name)
            
        for key, value in project.items():
            print "%s: %s" % (key, value)


# Script Output:
# MacBook:fedorahosted relrod$ python xmlrpc.py 
# scm: hg
# mailinglist: myProject-developers, myProject-commits
# name: myProject
# trac: yes
# mailing_lists: ['myProject-developers', 'myProject-commits']
# summary: myProject does X and Y, for the purpose of Z.
