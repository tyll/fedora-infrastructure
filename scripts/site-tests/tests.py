#!/usr/bin/python
# -*- coding: utf-8 -*-

color = { 'red' : '\x1b[0;31m',
        'green' : '\x1b[0;32m',
        'yellow' : '\x1b[1;33m',
        'white' : '\x1b[1;37m',
        'bold' : '\x1b[1m',
        'nobold' : '\x1b[22m',
        'default' : '\x1b[39m',
        'reset' : '\x1b[0m' }
OK = "%sOK%s" % (color['green'], color['reset'])
FAILED = "%sFAILED%s" % (color['red'], color['reset'])
WARNING = "%sWARNING%s" % (color['yellow'], color['reset'])

def is_normal(count, baseline, percent='10'):
  ''' Pass count and baseline and compare.  Throws warning if not in acceptable range'''
  baseline = float(baseline)
  diff = ((count / baseline) * 100) - 100
  if diff < 0:
    diff = diff * -1
  if diff > 10:
    return (WARNING, '%s is greater then %%%.4s of baseline.  (Maybe baseline needs an update?)', (count, diff))
  else:
    return (OK, '%s is within %%%.4s of baseline' % (count, diff))


class Headers():
  debug=None
  def __init__(self, debug=None):
      self.debug=debug
      return

  def check(self, headers, baseline):
      ''' Check the headers of a page for slowness or other errors '''
      if self.debug:
        print "\tProxy time: %s" % headers['proxytime'].split('=')[1]
        print "\tProxy server: %s" % headers['proxyserver']
        print "\tApp time: %s" % headers['apptime'].split('=')[1]
        print "\tApp server: %s" % headers['appserver']

      if headers['proxytime'].split('=')[1] > baseline:
          print "\t%s Proxy Time slower than baseline %s > %s" % (WARNING, headers['proxytime'].split('=')[1], baseline)
          return (WARNING, headers['proxytime'].split('=')[1])