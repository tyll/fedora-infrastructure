#!/usr/bin/python -t
VERSION = "2.5"

# $Id: review-stats.py,v 1.12 2010/01/15 05:14:10 tibbs Exp $
# Note: This script presently lives in internal git and external cvs.  External
# cvs is:
# http://cvs.fedoraproject.org/viewvc/status-report-scripts/review-stats.py?root=fedora
# or check it out with
# CVSROOT=:pserver:anonymous@cvs.fedoraproject.org:/cvs/fedora cvs co status-report-scripts
#
# Internal is in the puppet configs repository on puppet1.  It needs to be
# there so that puppet can distribute to the servers.  I recommend doing the
# work in the public cvs first, then copying to puppet's git after.

import bugzilla
import datetime
import glob
import operator
import os
import string
import sys
import tempfile
from copy import deepcopy
from genshi.template import TemplateLoader
from optparse import OptionParser

# Red Hat's bugzilla
url = 'https://bugzilla.redhat.com/xmlrpc.cgi'

# Some magic bug numbers
ACCEPT      = '163779'
NEEDSPONSOR = '177841'
GUIDELINES  = '197974'
SCITECH     = '505154'
LEGAL       = '182235'

# These will show up in a query but aren't actual review tickets
trackers = set([ACCEPT, NEEDSPONSOR, GUIDELINES, SCITECH])

def parse_commandline():
    usage = "usage: %prog [options] -d <dest_dir> -t <template_dir>"
    parser = OptionParser(usage)
    parser.add_option("-d", "--destination", dest="dirname",
              help="destination directory")
    parser.add_option("-f", "--frequency", dest="frequency",
              help="update frequency", default="60")
    parser.add_option("-t", "--templatedir", dest="templdir",
              help="template directory")
    parser.add_option("-u", "--url", dest="url",
              help="bugzilla URL to query",
              default=url)

    (options, args) = parser.parse_args()
    tst = str(options.dirname)
    if str(options.dirname) == 'None':
        parser.error("Please specify destination directory")
    if not os.path.isdir(options.dirname):
        parser.error("Please specify an existing destination directory")

    if str(options.templdir) == 'None':
        parser.error("Please specify templates directory")
    if not os.path.isdir(options.templdir):
        parser.error("Please specify an existing template directory")

    return options

def nobody(str):
    '''Shorten the long "nobody's working on it" string.'''
    if str == "Nobody's working on this, feel free to take it":
        return "(Nobody)"
    return str

def nosec(str):
    '''Remove the seconds from an hh:mm:ss format string.'''
    return str[0:str.rfind(':')]

def to_unicode(object, encoding='utf8', errors='replace'):
    if isinstance(object, basestring):
        if isinstance(object, str):
            return unicode(object, encoding, errors)
        else:
            return object
    return u''

def reporter(bug):
    '''Extract the reporter from a bug, replacing an empty value with "(none)".
    Yes, bugzilla will return a blank reporter for some reason.'''
    if (bug.reporter) == '':
        return "(none)"
    return bug.reporter

def yrmonth(str):
    '''Turn a bugzilla date into Month YYYY string.'''
    m = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
            'August', 'September', 'October', 'November', 'December']
    year = str.split('-')[0]
    month = int(str.split('-')[1])-1
    return m[month] + ' ' + year

def seq_max_split(seq, max_entries):
    """ Given a seq, split into a list of lists of length max_entries each. """
    ret = []
    num = len(seq)
    seq = list(seq) # Trying to use a set/etc. here is bad
    beg = 0
    while num > max_entries:
        end = beg + max_entries
        ret.append(seq[beg:end])
        beg += max_entries
        num -= max_entries
    ret.append(seq[beg:])
    return ret

def run_query(bz):
    querydata = {}
    bugdata = {}
    alldeps = set([])
    closeddeps = set([])

    querydata['column_list'] = ['opendate', 'changeddate', 'bug_severity',
            'alias', 'assigned_to', 'reporter', 'bug_status', 'resolution',
            'component', 'blockedby', 'dependson', 'short_desc',
            'status_whiteboard', 'flag_types']
    querydata['product'] = ['Fedora']
    querydata['component'] = ['Package Review']

    # Look up tickets with no flag set
    querydata['field0-0-0'] = 'flagtypes.name'
    querydata['type0-0-0'] = 'notregexp'
    querydata['value0-0-0'] = 'fedora-review[-+?]'
    bugs = filter(lambda b: str(b.bug_id) not in trackers, bz.query(querydata))

    for bug in bugs:
        bugdata[bug.bug_id] = {}
        bugdata[bug.bug_id]['hidden'] = 0
        bugdata[bug.bug_id]['blockedby'] = set(str(bug.blockedby).split(', '))-set([''])
        bugdata[bug.bug_id]['depends'] = set(str(bug.dependson).split(', '))-set([''])
        bugdata[bug.bug_id]['reviewflag'] = ' '

        # Keep track of dependencies in unflagged tickets
        alldeps |= bugdata[bug.bug_id]['depends']

    # Get the status of each dependency
    for i in seq_max_split(alldeps, 500):
        for bug in filter(None, bz.getbugssimple(i)):
            if bug.bug_status == 'CLOSED':
                closeddeps.add(str(bug.bug_id))

    # Some special processing for those unflagged tickets
    def opendep(id): return id not in closeddeps
    for bug in bugs:
        if (bug.bug_status != 'CLOSED' and
            (string.lower(bug.status_whiteboard).find('notready') >= 0
                    or string.lower(bug.status_whiteboard).find('buildfails') >= 0
                    or string.lower(bug.status_whiteboard).find('stalledsubmitter') >= 0
                    or LEGAL in bugdata[bug.bug_id]['blockedby']
                    or filter(opendep, bugdata[bug.bug_id]['depends']))):
            bugdata[bug.bug_id]['hidden'] = 1

    # Now process the other three flags; not much special processing for them
    querydata['type0-0-0'] = 'equals'
#    for i in ['-', '+', '?']:
    for i in ['-', '?']:
        querydata['value0-0-0'] = 'fedora-review' + i
        b1 = bz.query(querydata)
        for bug in b1:
            bugdata[bug.bug_id] = {}
            bugdata[bug.bug_id]['hidden'] = 0
            bugdata[bug.bug_id]['blockedby'] = []
            bugdata[bug.bug_id]['depends'] = []
            bugdata[bug.bug_id]['reviewflag'] = i
        bugs += b1

    bugs.sort(key=operator.attrgetter('bug_id'))

    return [bugs, bugdata]

    # Need to generate reports:
    #  "Accepted" and closed 
    #  "Accepted" but still open
    #    "Accepted" means either fedora-review+ or blocking FE-ACCEPT
    #  fedora-review- and closed
    #  fedora-review- but still open
    #  fedora-review? and still optn
    #  fedora-review? but closed
    #  Tickets awaiting review but which were hidden for some reason
    # That should be all tickets in the Package Review component

def write_html(loader, template, data, dir, fname):
    '''Load and render the given template with the given data to the given
       filename in the specified directory.'''
    tmpl = loader.load(template)
    output = tmpl.generate(**data)

    path = os.path.join(dir, fname)
    try:
        f = open(path, "w")
    except IOError, (err, strerr):
        print 'ERROR: %s: %s' % (strerr, path)
        sys.exit(1)

    f.write(output.render())
    f.close()

# Selection functions (should all be predicates)
def select_hidden(bug, bugd):
    if bugd['hidden'] == 1:
        return 1
    return 0

def select_merge(bug, bugd):
    if (bugd['reviewflag'] == ' '
            and bug.bug_status != 'CLOSED'
            and bug.short_desc.find('Merge Review') >= 0):
        return 1
    return 0

def select_needsponsor(bug, bugd):
    if (bugd['reviewflag'] == ' '
            and NEEDSPONSOR in bugd['blockedby']
            and bug.bug_status != 'CLOSED'
            and nobody(bug.assigned_to) == '(Nobody)'):
        return 1
    return 0

def select_new(bug, bugd):
    '''If someone assigns themself to a ticket, it's theirs regardless of
    whether they set the flag properly or not.'''
    if (bugd['reviewflag'] == ' '
            and bug.bug_status != 'CLOSED'
            and bugd['hidden'] == 0
            and nobody(bug.assigned_to) == '(Nobody)'
            and bug.short_desc.find('Merge Review') < 0):
        return 1
    return 0


# The data from a standard row in a bug list
def std_row(bug, rowclass):
    return {'id': bug.bug_id,
            'alias': to_unicode(bug.alias),
            'assignee': nobody(to_unicode(bug.assigned_to)),
            'class': rowclass,
            'lastchange': bug.changeddate,
            'status': bug.bug_status,
            'summary': to_unicode(bug.short_desc),
            }

# Report generators
def report_hidden(bugs, bugdata, loader, tmpdir, subs):
    data = deepcopy(subs)
    data['description'] = 'This page lists all review tickets are hidden from the main review queues'
    data['title'] = 'Hidden reviews'
    curmonth = ''

    for i in bugs:
        if select_hidden(i, bugdata[i.bug_id]):
            rowclass = 'bz_row_even'
            if NEEDSPONSOR in bugdata[i.bug_id]['blockedby']:
                rowclass = 'bz_state_NEEDSPONSOR'
            elif data['count'] % 2 == 1:
                rowclass = 'bz_row_odd'

            data['bugs'].append(std_row(i, rowclass))
            data['count'] +=1

    write_html(loader, 'plain.html', data, tmpdir, 'HIDDEN.html')

    return data['count']

def report_merge(bugs, bugdata, loader, tmpdir, subs):
    data = deepcopy(subs)
    data['description'] = 'This page lists all merge review tickets which need reviewers'
    data['title'] = 'Merge reviews'

    count = 0
    curmonth = ''

    for i in bugs:
        if select_merge(i, bugdata[i.bug_id]):
            rowclass = 'bz_row_even'
            if data['count'] % 2 == 1:
                rowclass = 'bz_row_odd'

            data['bugs'].append(std_row(i, rowclass))
            data['count'] +=1

    write_html(loader, 'plain.html', data, tmpdir, 'MERGE.html')

    return data['count']

def report_needsponsor(bugs, bugdata, loader, tmpdir, subs):
    # Note that this abuses the "month" view to group by reporter instead of month.
    data = deepcopy(subs)
    data['description'] = 'This page lists all new NEEDSPONSOR tickets (those without the fedora-revlew flag set)'
    data['title'] = 'NEEDSPONSOR tickets'
    curreporter = ''
    curcount = 0
    selected = []

    for i in bugs:
        if select_needsponsor(i, bugdata[i.bug_id]):
            selected.append(i)
    selected.sort(key=reporter)

    for i in selected:
        rowclass = 'bz_row_even'
        if data['count'] % 2 == 1:
            rowclass = 'bz_row_odd'

        if curreporter != reporter(i):
            data['months'].append({'month': reporter(i), 'bugs': []})
            curreporter = reporter(i)
            curcount = 0

        data['months'][-1]['bugs'].append(std_row(i, rowclass))
        data['count'] +=1
        curcount +=1

    write_html(loader, 'bymonth.html', data, tmpdir, 'NEEDSPONSOR.html')

    return data['count']

def report_new(bugs, bugdata, loader, tmpdir, subs):
    data = deepcopy(subs)
    data['description'] = 'This page lists new, reviewable package review tickets (excluding merge reviews).  Tickets colored green require a sponsor.'
    data['title'] = 'New package review tickets'

    curmonth = ''
    curcount = 0

    for i in bugs:
        if select_new(i, bugdata[i.bug_id]):
            rowclass = 'bz_row_even'
            if NEEDSPONSOR in bugdata[i.bug_id]['blockedby']:
                rowclass = 'bz_state_NEEDSPONSOR'
            elif data['count'] % 2 == 1:
                rowclass = 'bz_row_odd'

            if curmonth != yrmonth(i.opendate):
                if curcount > 0:
                    data['months'][-1]['month'] += (" (%d)" % curcount)
                data['months'].append({'month': yrmonth(i.opendate), 'bugs': []})
                curmonth = yrmonth(i.opendate)
                curcount = 0

            data['months'][-1]['bugs'].append(std_row(i, rowclass))
            data['count'] +=1
            curcount +=1

    if curcount > 0:
        data['months'][-1]['month'] += (" (%d)" % curcount)

    write_html(loader, 'bymonth.html', data, tmpdir, 'NEW.html')

    return data['count']

if __name__ == '__main__':
    options = parse_commandline()
    bz = bugzilla.Bugzilla(url=options.url)
    (bugs, bugdata) = run_query(bz)

    # Don't bother running this stuff until the query completes, since it fails
    # so often.
    loader = TemplateLoader(options.templdir)
    tmpdir = tempfile.mkdtemp(dir=options.dirname)

    # The initial set of substitutions that's shared between the report functions
    subs = {
            'update': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            'version': VERSION,
            'count': 0,
            'months': [],
            'bugs': [],
            }
    args = {'bugs':bugs, 'bugdata':bugdata, 'loader':loader, 'tmpdir':tmpdir, 'subs':subs}

    subs['new'] =         report_new(**args)
    subs['merge'] =       report_merge(**args)
    subs['needsponsor'] = report_needsponsor(**args)
    subs['hidden'] =      report_hidden(**args)
#    data['accepted_closed'] = report_accepted_closed(bugs, bugdata, loader, tmpdir)
#    data['accepted_open'] = report_accepted_open(bugs, bugdata, loader, tmpdir)
#    data['rejected_closed'] = report_rejected_closed(bugs, bugdata, loader, tmpdir)
#    data['rejected_open'] = report_rejected_open(bugs, bugdata, loader, tmpdir)
#    data['review_closed'] = report_review_closed(bugs, bugdata, loader, tmpdir)
#    data['review_open'] = report_review_open(bugs, bugdata, loader, tmpdir)
    write_html(loader, 'index.html', subs, tmpdir, 'index.html')

    for filename in glob.glob(os.path.join(tmpdir, '*')):
        newFilename = os.path.basename(filename)
        os.rename(filename, os.path.join(options.dirname, newFilename))

    os.rmdir(tmpdir)

    sys.exit(0)
