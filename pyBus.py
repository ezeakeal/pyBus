#!/usr/bin/python

import os, sys, time, signal, traceback
import pyBus_core as core

#####################################
# FUNCTIONS
#####################################
# Manage Ctrl+C gracefully
def signal_handler_quit(signal, frame):
  print 'Closing Serial Connection'
  core.closeBus()
  sys.exit(0)

# Print basic usage
def print_usage():
  print "Intended Use:"
  print "%s <PATH_TO_DEVICE>" % (sys.argv[0])
  print "Eg: %s /dev/ttyUSB0" % (sys.argv[0])

#####################################
# MAIN
#####################################
if len(sys.argv) != 2:
  print_usage()
  sys.exit(1)
# Startup and allow ctrl+c to be graceful
signal.signal(signal.SIGINT, signal_handler_quit)

# Load up the device
devPath = sys.argv[1]

# Read packets
while True:
  try:
    core.initialize(devPath)
    core.run()
  except Exception:
    core.printOut("I just hit some weird exception:", 2)
    traceback.print_exc(core.LOGFILE_ERROR)
    core.printOut("Going to sleep 5 seconds and restart", 2)
    time.sleep(5)
sys.exit(0)