#!/usr/bin/env python
# XML_RPC interface to "Hosting request" tickets on fedorahosted Trac.

# Project name: myProject
# 
# Project short summary: myProject does X and Y, for the purpose of Z.
# 
# SCM choice (git/bzr/hg/svn): hg
# 
# Project admin Fedora Account System account name: myAccountName
# 
# Yes/No, would you like a Trac instance for your project?: yes
# 
# Do you need a mailing list? If so, comma-separate a list of what you'd like them to be called. Otherwise, put "no": myProject-developers, myProject-commits

######################## Test ticket: 2172 ######################## 
# TODOs:
# - Make LOGFILE global.

import re, sys, os, urllib, xmlrpclib, random
import string, stat, pwd, grp, time
from fedora.client import *
from fedora.client.fas2 import *
from getpass import getpass
from optparse import OptionParser
from popen2 import popen2 as run_command

verbose = True
parser = OptionParser()
parser.add_option("-t", "--ticket", dest="ticket", help="The ticket number we want to work with.")
parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="Produce verbose output.")
(options, args) = parser.parse_args()

if options.ticket is None:
    print "[*] Please supply a ticket number with -t <number>"
    sys.exit()

print "Working with ticket #%s." % options.ticket

# Stuff for FedoraHosted only.
HOSTED_USERNAME = raw_input("Hosted Username: ")
HOSTED_PASSWORD = getpass("Hosted (Trac) Password: ")
#HOSTED_PASSWORD=''
HOSTED_SERVER='fedorahosted.org'
PROJECT_PATH='fedora-infrastructure'

# Stuff for FAS only -- when in production can probably be set to HOSTED_USERNAME and HOSTED_PASSWORD.
FAS_USERNAME='admin'
FAS_PASSWORD='admin'
FAS_SERVER='http://publictest3.fedoraproject.org/accounts' # Leave the /accounts at the end.

LOGFILE='./%s/log.txt' % os.path.dirname(__file__) # Same directory as the script.


class Repo:
    """ This class constructs the repo to be built. """
    
    def __init__(self, scm, ticket, projectname, groupname, logfile, commitlist):
        self.name = projectname
        self.group = groupname
        self.logfile = logfile
        self.ticketid = ticket[0]
        self.scm = scm
        self.commitlist = commitlist
    
    def log(self, status):
        """ Log actions done in the Repo class. """
        
        log = open(self.logfile, 'a')
        log.write("[" + self.ticketid + "] " + status + "\n")
        log.close()

        return status
    
    def groupWrite(self, path):
        # 1533: 256 | 128 | 64 | 32 | 16 | 8 | 1024 | 4 | 1
        #      O: R    W    X  G: R    W   X    +s  O: r x
        chmod = 1533
        os.chmod(path, chmod)
        for filename in os.listdir(path):
            filepath = os.path.join(path, filename)
            if os.path.isdir(filepath):
                self.groupWrite(filepath)
            else:
                os.chmod(filepath, chmod)
    
    def chownDir(self, username, group, path):
        uid = pwd.getpwnam(username)[2]
        gid = grp.getgrnam(group)[2]
        os.chown(path, uid, gid)
        for filename in os.listdir(path):
            filepath = os.path.join(path, filename)
            if os.path.isdir(filepath):
                self.chownDir(username,group,filepath)
            else:
                os.chown(filepath, uid, gid)
 
    def hg(self):
        """ Create an Hg repository. """
  	print 'Creating a Mercurial repo.'        
        # Initialize the repo.
        os.mkdir("/hg/" + self.name)
        os.chdir("/hg/" + self.name)
        run_command("hg init")
        
        # Set permissions on it.        
        self.groupWrite("/hg/" + self.name)
        self.chownDir("root", self.group, self.name)
        
        print "Created the Mercurial repo."
        self.log("Created a Mercurial repo.")
        
        #Do we need to set up a commit hook for a mailing list?
        if self.commitlist != "no": #Will it be passed as that?
            file = open("/hg/" + self.name + "/.hg/hgrc", 'w')
            file.write("[extensions]\nhgext.notify= \n")
            file.write("[hooks]\nchangegroup.notify = python:hgext.notify.hook\n")
            file.write("[email]\nfrom = admin@fedoraproject.org\n")
            file.write("[smtp]\nhost = localhost\n")
            file.write("[web]\nbaseurl = http://hg.fedoraproject.org/hg\n")
            file.write("[notify]\nsources = serve push pull bundle\n")
            file.write("test = False\n")
            file.write("config = /hg/" + self.name + "/.hg/subscriptions\n")
            file.write("maxdiff = -1\n")
            file.close()

            file = open("/hg/"+ self.name + "/.hg/subscriptions")
            file.write("[usersubs]\n" + self.commitlist + " = *\n")
            file.write("[reposubs]\n")
            file.close()

        return
    
    def git(self, description, owner):
        """ Create a Git repository. """
                
        # Initialize the repo.
        os.mkdir("/git/" + self.name + ".git")
        os.chdir("/git/" + self.name + ".git")
        run_command("git --bare init --shared=true")
        
        time.sleep(1)
        
        description_fh = open("/git/" + self.name + ".git/description", "w")
        description_fh.write(description)
        description_fh.close()
                
        # Set up the post-update hook (and run it once)
        os.remove("./hooks/post-update")
        os.symlink("/usr/bin/git-update-server-info", "./hooks/post-update")
        run_command("git update-server-info")
        
        # Permissions.
        self.groupWrite("/git/" + self.name + ".git")
        
        # TODO, remove this one day (not a priority: no user input)
        run_command("find . -perm /u+w -a ! -perm /g+w -exec chmod g+w \{\} \;")
        self.chownDir(owner, self.group, "/git/" + self.name + ".git")

        print "Created the git repo."
        self.log("Created a git repo.")

        if self.commitlist != "no":
            os.chdir("/git")
            f = open(self.name + ".git/commit-list", "w")
            f.write(self.commitlist)
            f.close()
            os.remove(self.name + ".git/hooks/update")
            os.symlink("/usr/bin/fedora/git-commit-mail-hook", self.name + ".git/hooks/update")
            
        return
    
    def bzr(self):
        """ Create a Bazaar repository (shared storage between branches). """
        
        os.mkdir("/bzr/" + self.name)
        os.chdir("/bzr/" + self.name)
        
        # Initialize repo.
        run_command("bzr init-repo . --no-trees")
        self.groupWrite("/bzr/" + self.name)
        self.chownDir("root", self.group, "/bzr/" + self.name)

        print "Created the bzr repo."
        self.log("Created a bzr repo.")
        return
        
    def svn(self):
        """ Create a subversion repository. """
        
        os.mkdir("/svn/" + self.name)
        os.chdir("/svn/" + self.name)
        
        # Initialize repo.
        run_command("svnadmin create .")
        self.chownDir("root", self.group, "/svn/" + self.name)
        self.groupWrite("/svn/" + self.name)

        print "Created the subversion repository."
        self.log("Created a subversion repo.")

        if self.commitlist != "no":
            os.chdir("/svn")
            #run_command("echo " + self.commitlist + " | tee " + self.name + "/commit-list > /dev/null")
            f = open(self.name + "/commit-list", "w")
            f.write(self.commitlist)
            f.close()
            os.symlink("/usr/bin/fedora/svn-commit-mail-hook ", self.name + "/hooks/update")
        return

class Group:
    def __init__(self, ticket, client, name, display_name, owner, group_type, logfile):
        
        self.client = client
        self.name = name
        self.display_name = display_name
        self.owner = owner
        self.group_type = group_type
        self.logfile = logfile
        self.ticketid = ticket[0]
    
    def log(self, status):
        """ Logs actions done in the Group creation class.. """
        log = open(self.logfile, 'a')
        log.write("[" + self.ticketid + "] " + status + "\n")
        log.close()

        return status
    
    def create(self):
        """ Creates an FAS group based on the information provided in __init__. """
        
        groupinfo = {}
        groupinfo['name'] = self.name
        groupinfo['display_name'] = self.display_name
        groupinfo['owner'] = self.owner
        groupinfo['group_type'] = self.group_type
        
        self.log("Sending request to /group/create")
        response = self.client.send_request('/group/create', groupinfo, auth=True)
        try:
            response['group']['id']
            self.log("Group creation: Success")
	    run_command("fasClient -i --force-refresh")
            return True
        except:
            self.log("Group creation: Failed to create %s [%s]" % (groupinfo['name'], response))
            return False
    

class Ticket:
    """ A class instance with methods to call for each hosting request ticket. """
    
    def __init__(self, ticket, logfile='', xmlrpc=''):
        self.ticket = ticket
        self.logfile = logfile
        self.id = ticket[0]
        self.xmlrpc = xmlrpc

        # For now, assume [3] will always be the dictionary.
        self.description = self.ticket[3]['description'].split("\n")
    
    project = {"mailing_lists": []}
    warnings = []
    
    def log(self, status):
        """ Log the current status to the logfile. """
        log = open(self.logfile, 'a')
        log.write("[" + self.id + "] " + status + "\n")
        log.close()
        
        return status
    
    def parse_line(self, search, shortname, line):
        """ The way this works is we search the line (for $search), and
        if we match, we split at the first colon. Everything after that is considered
        user input. We also do some on the fly validation here, simply so we don't have to call
        a valdiation function every time. It all gets done at the same time."""
        
        if search in line:
            fieldvalue = line.split(": ", 1)[1]
            
            # See if the user's response is blank.
            if fieldvalue == "":
                self.warnings.append("The '%s' field has a blank answer. Please answer all questions." % search)

            
            else:
                # Has a response, and the value validates.
                if shortname == 'name':
                    if len(fieldvalue) > 70:
                        self.warnings.append("The 'Project name' field should be less than 70 characters.")
                    
                    if not re.match(r'[\w\-\ ]+$', fieldvalue):
                        self.warnings.append("The 'Project name' field can only contain characters 0-9, a-z (upper/lowercase), <dash>, <space>, and <underscore>")
                        
                if shortname == 'summary':
                    if len(fieldvalue) > 1000:
                        self.warnings.append("Please make your entry for the 'Project short summary' field less than 1000 characters.")
                    if not re.match(r'[\w\-\ \.\,]+$', fieldvalue):
                        self.warnings.append("The 'Project short summary' field can only contain characters 0-9, a-z (upper/lowercase), <dash>, <space>, <underscore>, and <comma>.")
                    
                if shortname == 'scm':
		    print '"%s"' % fieldvalue
                    if not fieldvalue in ["git" ,"svn", "hg", "bzr"]:
                        self.warnings.append("Please make sure your scm choice is one of: git, svn, hg, bzr")
                
                if shortname == 'trac':
                    if fieldvalue.lower() != ("yes" or "no"):
                        self.warnings.append("Please answer 'yes' or 'no' as to whether or not you need a Trac instance.")
   
                if shortname == 'mailinglist':
                    if fieldvalue.lower() != "no":
                        self.mailinglists = True
                        if not re.match(r'[\w\-\ \,]+$', fieldvalue):
                            self.warnings.append("The 'mailing list' field can only contain characters 0-9, a-z (upper/lowercase), <dash>, <space>, <underscore>, and <comma>.")
                    else:
                        self.mailinglists = False
                
                if shortname == 'commitnotices':
                    if fieldvalue.lower() != "no":
                        if not re.match(r'([0-9a-z\.\+\-]+)@(?:lists.fedoraproject.org|lists.fedorahosted.org)', fieldvalue.lower()):
                            self.warnings.append("The commit notices list must be hosted by the Fedora Project (i.e ending with @lists.fedoraproject.org or @lists.fedorahosted.org address") 

                self.project[shortname] = fieldvalue

    
    def parse_ticket(self):
        """ This function actually makes the calls to parse_line() and puts the
        content of the ticket into values that we can work with. That's all this does. """
        
        self.log("Parsing ticket.")
        
        for line in self.description:
            self.parse_line("Project name", "name", line)
            self.parse_line("Project short summary", "summary", line)
            self.parse_line("SCM choice", "scm", line)
            self.parse_line("Trac instance", "trac", line)
            self.parse_line("mailing list", "mailinglist", line)
            self.parse_line("Send commits", "commitnotices", line)
        
        self.project['group'] = (self.project['scm'] + (self.project['name'].replace(" ",""))).lower()
        self.project['owner'] = self.ticket[3]['reporter']
    
    def handle_mailing_lists(self):
        """ The purpose of this function is to see whether or not a user
        wants a mailing list, and if they do, add those to a list, so we
        can create them all. (self.create_mailing_lists())"""
        
        self.log("Dealing with mailing lists (not creating yet).")
        
        if self.mailinglists:
            lists = self.project['mailinglist'].split(",")
            for req_list in lists:
                req_list = req_list.replace(" ", "")
                self.project['mailing_lists'].append(req_list)
    
    def post_warnings(self):
        """ This method takes all the warnings in self.warnings and puts them in a comment on the ticket. """
        
        self.log("Posting warnings to the ticket.")
        
        comment = "Please fix the following issues, and create a *new* ticket. Please do not re-open already-processed tickets.\n\n"

        for warning in self.warnings:
            comment += "- " + warning + "\n"
            self.log("Warning: " + warning)

        self.xmlrpc.ticket.update(self.id, comment, {'resolution': 'Waiting on User Input', 'status': 'closed'})
        
        return
    
    def decide(self):
        """ This method decides whether or not a project gets added. """
        
        if len(self.warnings) > 0:
            self.log("Decided negatively on accepting the ticket.")
            return False
        else:
            self.log("Decided positively on accepting the ticket.")
            return True
    
    def add_project(self):
        
        self.log("Adding the project.")
        run_command("sudo /usr/local/bin/hosted-setup.sh '%s' '%s' '%s'" % (self.project['name'], self.project['owner'], self.project['scm']))
        comment = "The project has been automatically created.\n"
        comment += "If there are any issues, please comment on this ticket."
        
        self.xmlrpc.ticket.update(self.id, comment, {'resolution': 'Project Created', 'status': 'closed'})
        return

class MailingList:
    def __init__(self, username, client):
        self.username = username
        self.client = client
    
    def getClientEmail(self):
        response = self.client.person_by_username(self.username)
        return response['email']
    
    def generatePassword(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(random.randint(10,20)))
    
    def create(self, name, email, password):
        run_command("sudo /usr/lib/mailman/bin/newlist %s %s %s" % (name, self.getClientEmail, password))

#for ticket in xmlrpc.ticket.query("summary=^Hosting request&status=new|open"):
print "Connecting to the Trac XMLRPC."
xmlrpc = xmlrpclib.ServerProxy("https://%s:%s@%s/%s/login/xmlrpc" % (
    urllib.quote(HOSTED_USERNAME), urllib.quote(HOSTED_PASSWORD), HOSTED_SERVER, PROJECT_PATH))

ticket_id = xmlrpc.ticket.get(options.ticket)

ticket = Ticket(ticket_id, logfile=LOGFILE, xmlrpc=xmlrpc)
ticket.parse_ticket()

accepted = ticket.decide()
if accepted:
    # Create an FAS object.
    client = AccountSystem(FAS_SERVER, username=FAS_USERNAME, password=FAS_PASSWORD)
    
    # Create the group.
    group = Group( ticket_id, client, ticket.project['group'], ticket.project['name'],
        ticket.project['owner'], ticket.project['scm'], LOGFILE)
    group.create()
    
    # Meh, deal with mailing lists.
    ticket.handle_mailing_lists()
    mlist = MailingList(ticket.project['owner'], client)
    owner_email = mlist.getClientEmail()
    for mailinglist in ticket.project['mailing_lists']:
        password = mlist.generatePassword()
        mlist.create(mailinglist, owner_email, password)
    
    # Create the repository.
    repo = Repo(ticket.project['scm'], ticket_id, ticket.project['name'], ticket.project['group'], LOGFILE, ticket.project['commitnotices'])
    print "SCM: %s" % ticket.project['scm']
    if ticket.project['scm'] == 'git': repo.git(ticket.project['summary'], ticket.project['owner'])
    elif ticket.project['scm'] == 'hg': repo.hg()
    elif ticket.project['scm'] == 'bzr':  repo.bzr()
    elif ticket.project['scm'] == 'svn': repo.svn()

    # Add the project.
    ticket.add_project()

else:
    ticket.post_warnings()

if verbose:
    for key, value in ticket.project.items():
        print "%s: %s" % (key, value)


