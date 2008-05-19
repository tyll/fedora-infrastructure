#!/usr/bin/python -tt
'''
Licensed under the GNU GPL v2.

Some pretty awful python code to give details about our postgres databases
I would have written this in bad perl but my perl was too rusty.

This script detects when a new database is added to the system.

Note:
If this is run on a database that hasn't had the pgstattuple function added
into template1, pgstattuple will have to be added to template1 and each
existing database.  Future databases will inherit pgstattuple from template1.

yum install -y postgresql-contrib
sudo -u postgres psql </usr/share/pgsql/contrib/pgstattuple.sql DBNAME

'''
__version__ = '0.5'

import sys
import os
import re
import cPickle
import glob
import subprocess
import tempfile
import datetime
from stat import ST_MTIME
from subprocess import Popen, PIPE
import optparse
import fcntl

IGNOREDDBS = ('postgres', 'template1', 'template0')
STATEDIR = '/var/lib/vacstat'

class DBError(Exception):
    pass

class SchemaChangeError(DBError):
    pass

class InitialRunWarning(SchemaChangeError):
    pass

class ArgumentError(Exception):
    pass

class XIDOverflowWarning(DBError):
    pass

def _compare_db(dbTables, opts):
    '''Verify the db tables are the same as the last run.
    '''
    # Load the currently known tables
    try:
        knownFile = file(os.path.join(opts.statedir, 'knowndbs.pkl'), 'r')
    except IOError:
        knownFile = file(os.path.join(opts.statedir, 'knowndbs.pkl'), 'w')
        cPickle.dump(dbTables, knownFile)
        knownFile.close()
        raise InitialRunWarning, 'No databases currently setup at this location.  Be sure to setup an initial vacuum policy for all databases from this script'

    knownTables = cPickle.load(knownFile)
    knownFile.close()

    results = []
    # First check that we haven't dropped any dbs
    for db in knownTables:
        if db not in dbTables:
            results.append('%s has been removed' % db)
        for table in knownTables[db]:
            if table not in dbTables[db]:
                results.append('table %s has been removed from %s' % (table, db))

    # Then check that we haven't added any
    for db in dbTables:
        if db not in knownTables:
            results.append('db %s has been added' % db)
            continue
        for table in dbTables[db]:
            if table not in knownTables[db]:
                results.append('db %s has a new table %s' % (db, table))

    if results:
        unknowns = file(os.path.join(opts.statedir, 'unknowndbs.pkl'), 'w')
        cPickle.dump(dbTables, unknowns)
        unknowns.close()
        msg = '''The database schema has changed since the last run.

Please make sure that the following databases and tables are setup to be
vacuumed.  Then move the file %s/unknowndbs.pkl to %s/knowndbs.pkl

%s
        ''' % (opts.statedir, opts.statedir, '\n'.join(results))
        raise SchemaChangeError, msg

def test_schema(opts):
    '''Test that the database schema is known.  This helps us keep the
    vacuum policy up-to-date by forcing us to acknowledge all changes before
    they can be used.
    '''
    dbnameRE = re.compile('^[ \t]+([^ \t]+)[ \t]+\|')
    tablenameRE = re.compile('^[^|]+\|[ \t]+([^ \t]+)[ \t]+\|')

    psqlCmd = subprocess.Popen(('/usr/bin/psql', 'postgres'),
            stdout=PIPE, stdin=PIPE)
    output = psqlCmd.communicate('\\l\n')[0].split('\n')
    dbTables = {}
    for db in output[3:-3]:
        match = dbnameRE.match(db)
        if match.group(1):
            if match.group(1) in IGNOREDDBS:
                continue
            dbTables[match.group(1)] = []
        else:
            raise SchemaChangeError, 'Regular Expression did not detect db'
   
    for db in dbTables:
        psqlCmd = subprocess.Popen(('/usr/bin/psql', db),
                stdout=PIPE, stdin=PIPE)
        output = psqlCmd.communicate('\\dt\n')[0].split('\n')
        for table in output[3:-3]:
            match = tablenameRE.match(table)
            if match.group(1):
                dbTables[db].append(match.group(1))
            else:
                raise SchemaChangeError, 'Regular Expression did not detect table for %s' % db

    # Make sure we're only dealing with known databases
    _compare_db(dbTables, opts)

def test_transactions(opts):
    dbXIdRE = re.compile('^[ \t]+([^ \t]+).*[ \t]+([0-9]+)$')
    psqlCmd = subprocess.Popen(('/usr/bin/psql'), stdout=PIPE, stdin=PIPE)
    output = psqlCmd.communicate('select datname, age(datfrozenxid), pow(2, 31) - age(datfrozenxid) as xids_remaining from pg_database;\n')[0].split('\n')
    overflows = []
    for dbLine in output[2:-3]:
        match = dbXIdRE.match(dbLine)
        if match.group(1) and match.group(2):
            if int(match.group(2)) <= 500000000:
                overflows.append('Used over half the transaction ids for %(db)s.  Please schedule a vacuum of that entire database soon:\n  sudo -u postgres vacuumdb -zvd %(db)s' % {'db': match.group(1)})
        else:
            raise DBError, 'Unexpected string received when testing for transaction overflow:\n %s' % dbLine

    if overflows:
        raise XIDOverflowWarning, '\n'.join(overflows)

def test_all(opts):
    test_transactions(opts)
    test_schema(opts)

def list_dbs(opts):
    # Read in the DBs we are already aware of
    if not os.access(os.path.join(opts.statedir, 'knowndbs.pkl'), os.F_OK):
        try:
            test_schema(opts)
        except InitialRunWarning, e:
            # This is expected to be the initial run
            print e

    knownFile = file(os.path.join(opts.statedir, 'knowndbs.pkl'), 'r')
    knownDBs = cPickle.load(knownFile)
    knownFile.close()
    print 'Databases: %s\n' % knownDBs.keys()
    for db in knownDBs:
        print '  %s tables:' % db
        print '    %s' % knownDBs[db]
        print

def _st_run(interval, stats, db, table, sessionDir):
    # When the optionList says we're going to set stattuple-hour to
    # be invoked we know that we're presently on stattuple-start.
    if interval == 'initial':
        # Run a vacuum of the database table if this is the first time
        psqlCmd = subprocess.Popen(
                ('/usr/bin/psql', 'postgres', '-d', db),
                stdout=PIPE, stdin=PIPE, env={'PGOPTIONS':'-c maintenance_work_mem=1048576'})
        psqlCmd.communicate('vacuum analyze %s\n' % table)
        if psqlCmd.returncode:
            raise DBError, 'Vacuum failed on %s %s' % (db, table)
    
    # Set an at job to invoke the next stattuple job
    if interval != 'day':
        command = ['/usr/bin/at']
        if interval == 'initial':
            command.append('now + 1 hours')
        elif interval == 'hour':
            command.append('now + 5 hours')
        elif interval == 'quarter':
            command.append('now + 18 hours')
        else:
            raise Exception, 'Unknown interval %s' % interval
        atCmd = subprocess.Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        command = [os.path.abspath(sys.argv[0])]
        command.extend(('--session', opts.sessionID, '--database',
                db, '--table', table))
        command.extend(opts.optionList)
        atCmd.stdin.write(' '.join(command))
        atCmd.stdin.close()
        if atCmd.wait():
            print 'Scheduling interval after %s for %s:%s failed' % (interval, db, table)

    # Run stattuple of the tables in the db.
    psqlCmd = subprocess.Popen(('/usr/bin/psql', 'postgres', '-d', db), stdout=PIPE, stdin=PIPE)
    output = psqlCmd.communicate("\\x\nselect * from pgstattuple('%s')\n" % table)[0].split('\n')
    for line in output[2:-2]:
        key, value = line.split(' | ')
        value = value.strip()
        if value.find('.') >= 0:
            value = float(value)
        else:
            value = int(value)
        stats[db][table][interval][key.strip()] = value

def stattuple(opts):
    '''Start a stattuple run.
        
    This gathers initial statistics on how much updating is being seen on a
    database's tables.
    '''
    # Ah, what I wouldn't give for functools.partial()
    interval = 'day'
    if opts.optionList:
        if opts.optionList[0].endswith('-hour'):
            interval = 'initial'
        elif opts.optionList[0].endswith('-quarter'):
            interval = 'hour'
        elif opts.optionList[0].endswith('-day'):
            interval = 'quarter'


    # Read in the DBs we are already aware of
    if not os.access(os.path.join(opts.statedir, 'knowndbs.pkl'), os.F_OK):
        try:
            test_schema(opts)
        except InitialRunWarning, e:
            # This is expected to be the initial run
            print e

    knownFile = file(os.path.join(opts.statedir, 'knowndbs.pkl'), 'r')
    knownDBs = cPickle.load(knownFile)
    knownFile.close()

    if opts.databases:
        dbList = opts.databases
    else:
        # If no database is selected, we'll collect statistics on all of them
        dbList = knownDBs.keys()

    # Make sure we have a schema for all requested dbs
    for db in dbList:
        if db not in knownDBs:
            raise ArgumentsError, 'Cannot process unknown DB, %s.  Perhaps you need to run "vacstat.py schema" first' % db

    if opts.tables:
        # Make sure we have a schema for all requested tables
        if len(dbList) != 1:
            raise ArgumentsError, '--tables can only be used if --databases is specified exactly once.'
        for table in opts.tables:
            if table not in knownDBs[dbList[0]]:
                raise  ArgumentsError, 'Cannot process unknown Table %s which is not in db %s.  Perhaps you need to run "vacstat.py schema" first' % (table, db)
        tableList = opts.tables
    else:
        tableList = None
    
    # Intialize the data struct we'll be saving all our information in
    stats = {}
    for db in dbList:
        stats[db] = {}
        for table in knownDBs[db]:
            stats[db][table] = {'initial':{},
                'hour':{}, 'quarter':{}, 'day':{}}
    # If this is our first time, initialize a new outputDir
    if not opts.sessionID:
        sessionDir = tempfile.mkdtemp(prefix=datetime.datetime.today().strftime('stattuple-%Y%m%d%H%M%S.'), dir=opts.statedir)
        opts.sessionID = os.path.basename(sessionDir)
        statsFile = file(os.path.join(sessionDir, 'stats.pkl'), 'w')
        cPickle.dump(stats, statsFile)
        statsFile.close()
    else:
        sessionDir = os.path.join(opts.statedir, opts.sessionID
)
    if tableList:
        db = dbList[0]
        for table in tableList:
            _st_run(interval, stats, db, table, sessionDir)
    else:
        for db in dbList:
            for table in knownDBs[db]:
                _st_run(interval, stats, db, table, sessionDir)

    # Load the current pickled data
    statsFile = file(os.path.join(sessionDir, 'stats.pkl'), 'rb+')
    fcntl.lockf(statsFile, fcntl.LOCK_EX)
    persistentStats = cPickle.load(statsFile)
    # Merge old and new information
    for db in stats:
        for table in stats[db]:
            for period in stats[db][table]:
                if stats[db][table][period]:
                    persistentStats[db][table][period] = stats[db][table][period]
    # save merged information back to the statsFile
    statsFile.truncate(0)
    statsFile.seek(0)
    cPickle.dump(persistentStats, statsFile)
    statsFile.flush()
    fcntl.lockf(statsFile, fcntl.LOCK_UN)
    statsFile.close()

    if interval == 'day':
        # add the db:table to a file to show we're done gathering stats
        done = file(os.path.join(sessionDir, 'DONE'), 'a')
        fcntl.lockf(done, fcntl.LOCK_EX)
        done.write('%s:%s\n' % (opts.databases[0], opts.tables[0]))
        fcntl.lockf(done, fcntl.LOCK_UN)
        done.close()

def merge_history(statedir):
    statDirList = sorted(glob.glob(os.path.join(statedir, 'stattuple-*')))
    for statDir in statDirList:
        finishedTables = {}
        timestamp = 0 # When the stat collection finished
        # Read data from each session directory.
        if not os.path.isdir(statDir):
            # Sanity check that this is an output dir
            continue
        if glob.glob(os.path.join(statDir, 'DONE')):
            # Read in the tables
            finishFile = file(os.path.join(statDir, 'DONE'), 'r')
            fcntl.lockf(finishFile, fcntl.LOCK_SH)
            # Get the timestamp from the finish file for later
            timestamp = os.stat(os.path.join(statDir, 'DONE'))[ST_MTIME]
            for line in finishFile:
                (db, table) = line.strip().split(':')
                if db not in finishedTables:
                    finishedTables[db] = {}
                if table not in finishedTables[db]:
                    finishedTables[db][table] = {}
            fcntl.lockf(finishFile, fcntl.LOCK_UN)
            finishFile.close()
        else:
            # This one is not done yet
            continue

        # Read the tables from the stat file
        statsFile = file(os.path.join(statDir, 'stats.pkl'), 'r')
        fcntl.lockf(statsFile, fcntl.LOCK_SH)
        stats = cPickle.load(statsFile)

        fcntl.lockf(statsFile, fcntl.LOCK_UN)
        statsFile.close()
        
        # Check that all tables are done
        finished = True
        for db in stats:
            if db not in finishedTables:
                finished = False
                break
            for table in stats[db]:
                if table not in finishedTables[db]:
                    finished = False
                    break
            if not finished:
                break
        del finishedTables
        if not finished:
            continue

        #
        # Add a new record to our history file
        #
        historyFilename = os.path.join(statedir, 'history.pkl')
        # If the file doesn't exist yet, create it
        if not os.access(historyFilename, os.F_OK):
            history = {}
            historyFile = file(historyFilename, 'w')
            fcntl.lockf(historyFile, fcntl.LOCK_EX)
            cPickle.dump(history, historyFile)
            fcntl.lockf(historyFile, fcntl.LOCK_UN)
            historyFile.close()

        historyFile = file(os.path.join(statedir, 'history.pkl'), 'rb+')
        fcntl.lockf(historyFile, fcntl.LOCK_EX)
        history = cPickle.load(historyFile)

        # Merge the data we've read in with the historical data
        for db in stats:
            if db not in history:
                history[db] = {}
            for table in stats[db]:
                if table not in history[db]:
                    history[db][table] = {}
                history[db][table][timestamp] = {}
                for interval in stats[db][table]:
                    history[db][table][timestamp][interval] = {}
                    for key, value in stats[db][table][interval].items():
                        if isinstance(value, str):
                            if value.find('.') >= -1:
                                history[db][table][timestamp][interval][key] = float(value)
                            else:
                                history[db][table][timestamp][interval][key] = int(value)
                        else:
                            history[db][table][timestamp][interval][key] = value

        historyFile.truncate(0)
        historyFile.seek(0)
        cPickle.dump(history, historyFile)
        fcntl.lockf(historyFile, fcntl.LOCK_UN)
        historyFile.close()

        # Delete the processed stattuple directory

def analyze_data(opts):
    merge_history(opts.statedir)

    # Read in the history
    historyFile = file(os.path.join(opts.statedir, 'history.pkl'), 'r')
    fcntl.lockf(historyFile, fcntl.LOCK_SH)
    history = cPickle.load(historyFile)
    fcntl.lockf(historyFile, fcntl.LOCK_UN)
    historyFile.close()

    hourly = []
    daily = []
    suggestions = []
    for db in history:
        for table in history[db]:
            # find latest timestamp for this table
            last = sorted(history[db][table].keys())[-1]
            tableData = []
            run = history[db][table][last]

            #
            # Battery of tests
            #

            infrequent = False
            frequent = False
            vacuumFull = False

            if run['day']['free_space'] == 0 and \
                    run['day']['dead_tuple_len'] == 0 \
                    and run['day']['table_len'] == 0:
                # This table is empty
                infrequent = True

            # Check how much dead tuples grew absolutely in 24 hours
            if run['day']['dead_tuple_len'] <= 10000:
                infrequent = True
            elif run['day']['dead_tuple_len'] >= 1000000:
                frequent = True

            # Check how many dead vs live tuples there are
            if run['day']['dead_tuple_len'] + run['day']['tuple_len'] == 0:
                deadTuplePercent = 0
            else:
                deadTuplePercent = run['day']['dead_tuple_len'] * 100.0 \
                        / (run['day']['dead_tuple_len'] \
                        + run['day']['tuple_len'])
            if deadTuplePercent > 20:
                frequent = True
            elif deadTuplePercent < 10:
                infrequent = True

            # Check how much free space exists
            if run['day']['free_space'] + run['day']['tuple_len'] \
                    + run['day']['dead_tuple_len'] == 0:
                freeSpacePercent = 0
            else:
                freeSpacePercent = (run['day']['free_space'] \
                        + run['day']['dead_tuple_len']) * 100.0 \
                        / (run['day']['free_space'] + run['day']['tuple_len'] \
                        + run['day']['dead_tuple_len'])
            # If free space is larger than 15%, see whether we can use that
            # much space between vacuums (Build in a small margin for tables
            # that are so small that the free space from the table being
            # allocated is > 15%.)
            if freeSpacePercent > 15 and run['day']['table_len'] > 524288:
                if frequent:
                    # Calculate roughly how much is used per hour.  Take the
                    # maximum of our samples
                    usage = (run['initial']['free_space'] - run['day']['free_space'])/24.0
                    if usage < run['initial']['free_space'] - run['hour']['free_space']:
                        usage = run['hour']['free_space'] - run['hour']['free_space']
                    if usage < (run['initial']['free_space'] - run['quarter']['free_space']) / 6:
                        usage = (run['initial']['free_space'] - run['quarter']['free_space']) / 6
                else:
                    # Calculate how much is used per day
                    usage = run['initial']['free_space'] - run['day']['free_space']
                # If the projected usage between vacuums is < the amount of
                # free space we have, recommend a vacuum full.
                if usage < run['day']['free_space']:
                    suggestions.append('Vacuum full %(db)s %(table)s: Freespace Percent %(freeP)s%%, %(freeB)s Bytes\n  vacuumdb -zfd %(db)s -t %(table)s' % {'db': db, 'table': table, 'freeP': freeSpacePercent, 'freeB': run['day']['free_space']})
           
            # if a table is large in absolute terms, flag them as
            # potentially problematic
            # 5GB  (For reference, mirrormanager::host_category_dir==1.2GB
            # koji::rpmfiles == 20GB)
            if run['day']['table_len'] >= 5000000000:
                suggestions.append('%s %s is quite large and may cause problems' % (db, table))
       
            # Output suggestions
            # Currently we only suggest hourly and daily
            if frequent:
                hourly.append((db, table))
            else:
                daily.append((db, table))

    print 'hourly cron script:'
    print '#!/bin/sh'
    print
    print "PGOPTIONS='-c maintenance_work_mem=1048576'"
    print
    for table in hourly:
        print '/usr/bin/vacuumdb -z --quiet -d %s -t %s' % (table[0], table[1])

    print '\n\ndaily cron script:'
    print '#!/bin/sh'
    print
    print "PGOPTIONS='-c maintenance_work_mem=1048576'"
    print
    for table in daily:
        print '/usr/bin/vacuumdb -z --quiet -d %s -t %s' % (table[0], table[1])

    print 'Things to look into further:'
    for line in suggestions:
        print line

Commands = {'schema': test_schema,
    'transactions': test_transactions,
    'check': test_all,
    'list': list_dbs,
    'stattuple-start': stattuple,
    'stattuple-hour': stattuple,
    'stattuple-quarter': stattuple,
    'stattuple-day': stattuple,
    'analyze': analyze_data}

def parse_args():
    '''Take information from the user about what actions to perform.
    '''
    parser = optparse.OptionParser(version = __version__, usage='''
vacstat.py COMMAND [options]

COMMAND can be::
  transactions:     check that we aren't in danger of running out of
                    transaction ids.
  schema:           check that the database schema hasn't changed since the
                    last run.  This helps you keep the vacuum policy up to
                    date by showing you what tables/databases have changed
                    since the last run.
  check:            run schema and transactions checks.
  list:             List dbs and tables that are known.
  stattuple-start:  Start a stattuple run.  This command should be used with
                    the --database option to prevent overloading the database
                    server with too many queries at the same time.
                    stattuple-start will run a vacuum of the database/tables
                    followed by a stattuple of the tables in the db.  It will
                    save the stattuple output to directories under --statedir
                    and then set an at job to reinvoke itself in an hour
                    with the stattuple-hour command.
  analyze:          *** Unimplemented *** This command should take information
                    in --statedir and produce a graph of tuple growth over
                    time and recomendation for how frequently to vacuum.

  ** The following commands are used internally and won't produce meaningful
  ** statistics by themselves.  Run stattuple-start instead.

  stattuple-hour:   Used internally by stattuple-start to run stattuple on
                    certain databases/tables an hour after vacuuming.  The
                    stattuple output will be saved to --statedir and then it
                    will set an at job to reinvoke itself in five more hours
                    with the stattuple-quarter command.
  stattuple-quarter:Used internally by stattuple-hour to run stattuple on
                    certain databases/tables 6 hours after vacuuming.  The
                    stattuple output will be saved to --statedir and then it
                    will set an at job to reinvoke itself in 18 hours.
  stattuple-day:    Used internally by stattuple-quarter to run stattuple on
                    certain databases/tables 6 hours after vacuuming.  The
                    stattuple output will be saved to --statedir and then
                    exit.
''')
    parser.add_option('-s', '--state-dir',
        dest='statedir',
        action='store',
        default=STATEDIR,
        help='Directory to get and store information about databases/tables')
    parser.add_option('-d', '--database',
        dest='databases',
        action='append',
        default=[],
        help='Database to process.  You can specify this option multiple times.  Defaults to all')
    parser.add_option('-t', '--table',
        dest='tables',
        action='append',
        default=[],
        help='Tables to process.  This option can only be used if --databases is used to specify exactly one database.  You can specify this option multiple times.  Defaults to all')
    parser.add_option('--session',
        dest='sessionID',
        action='store',
        default='',
        help='Internal command line option to pass data between invocations of the program.')

    (opts, args) = parser.parse_args()

    # Check that we were given a proper command
    if len(args) < 1:
        raise ArgumentError, 'No command specified'
    elif len(args) > 1:
        raise ArgumentError, 'Can only specify one command'
    if args[0] not in Commands:
        raise ArgumentError, 'Unknown Command'

    if opts.tables and len(opts.databases) != 1:
        raise ArgumentError, '--tables can only be used if --databases is specified exactly once.'

    if args[0] in ('schema', 'list', 'check', 'transactions'):
        if opts.databases:
            raise ArgumentError, 'schema, list, transactions, and check commands cannot be used with --database'

    # optionList is used to reinvoke the new stattuple
    opts.optionList = []
    if args[0].startswith('stattuple') and not args[0].endswith('-day'):
        if args[0].endswith('-start'):
            opts.optionList.append('stattuple-hour')
        elif args[0].endswith('-hour'):
            opts.optionList.append('stattuple-quarter')
        elif args[0].endswith('-quarter'):
            opts.optionList.append('stattuple-day')
        opts.optionList.extend(('-s', opts.statedir))

    return args[0], opts

def init_statedir(statedir):
    # Make sure the statedir is ready
    if not os.path.isdir(statedir):
        try:
            os.makedirs(statedir)
        except:
            raise IOError, 'You do not have permission to create the statedir %s' % statedir
    
    if not os.access(statedir, os.R_OK | os.X_OK | os.W_OK):
        raise IOError, 'You do not have permission to use %s as the statedir' % statedir

if __name__ == '__main__':
    command, opts = parse_args()

    init_statedir(opts.statedir)
    Commands[command](opts)

    sys.exit(0)
