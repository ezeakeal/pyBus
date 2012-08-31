#!/usr/bin/python

import os, sys, time, signal

sys.path.append( './lib/' )

import pyBus_module_web as pB_web
import pyBus_core as core

#####################################
# FUNCTIONS
#####################################
# Print basic usage
def print_usage():
  print "Intended Use:"
  print "%s <BROADCAST ADDRESS>" % (sys.argv[0])
  print "Eg: %s 0.0.0.0:8815" % (sys.argv[0])

#####################################
# MAIN
#####################################
if len(sys.argv) != 2:
  print_usage()
  sys.exit(1)

# Run web interface
pB_web.init()

sys.exit(0)