#!/usr/bin/python

import os, sys, time, signal, traceback, logging, argparse
import pyBus_core as core

#####################################
# FUNCTIONS
#####################################
# Manage Ctrl+C gracefully
def signal_handler_quit(signal, frame):
  logging.info("Shutting down pyBus")
  core.shutdown()
  sys.exit(0)

# Print basic usage
def print_usage():
  print "Intended Use:"
  print "%s <PATH_TO_DEVICE>" % (sys.argv[0])
  print "Eg: %s /dev/ttyUSB0" % (sys.argv[0])

def configureLogging(numeric_level):
  logfile = core.LOGFILE
  if not isinstance(numeric_level, int):
    numeric_level=2
  logging.basicConfig(
    filename=logfile, 
    level=numeric_level,
    format='%(asctime)s [%(levelname)s in %(module)s] %(message)s', 
    datefmt='%Y/%m/%dT%I:%M:%S'
  )
  
def createParser():
  parser = argparse.ArgumentParser()
  parser.add_argument('-v', '--verbose', action='count', default=0, help='Increases verbosity of output')
  parser.add_argument('device', action='store', help='Path to iBus USB interface (reslers.de)')
  return parser
#####################################
# MAIN
#####################################
parser = createParser()
results = parser.parse_args()
loglevel      = results.verbose

signal.signal(signal.SIGINT, signal_handler_quit)
configureLogging(loglevel)

devPath = sys.argv[1]
while True:
  try:
    core.initialize(devPath)
    core.run()
  except Exception:
    logging.error("I just hit some weird exception:")
    logging.error(traceback.format_exc())
    logging.info("Going to sleep 5 seconds and restart")
    time.sleep(5)
sys.exit(0)