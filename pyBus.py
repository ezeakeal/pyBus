#!/usr/bin/python

import os, sys, time, signal, traceback, logging, argparse, gzip
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

def compress_old_truncate():
  logfile = core.LOGFILE
  compressed_filename = logfile + '.gz'
  num_append = 1
  while os.path.exists("%s.%s" %(compressed_filename, num_append)):
    num_append = num_append + 1
  compressed_filename = "%s.%s" %(compressed_filename, num_append)
  f_in = open(logfile, 'rw')
  try:
    f_out = gzip.open(compressed_filename, 'wb')
    f_out.writelines(f_in)
    f_out.close()
  except:
    logging.critical("There has been an error archiving log file!")
  f_in.close()
  f_in = open(logfile, 'w')
  f_in.truncate()
  f_in.close()
  
#################################
# Configure Logging for pySel
#################################
def configureLogging(numeric_level):
  logfile = core.LOGFILE
  if os.path.exists(logfile):
    compress_old_truncate()
  if not isinstance(numeric_level, int):
    numeric_level=0
  logging.basicConfig(
    filename=logfile, 
    level=numeric_level,
    format='%(asctime)s [%(levelname)s in %(module)s] %(message)s', 
    datefmt='%Y/%m/%dT%I:%M:%S'
  )
  
def createParser():
  parser = argparse.ArgumentParser()
  parser.add_argument('-v', '--verbose', action='count', default=0, help='Increases verbosity of logging. See LOGFILE variable.')
  parser.add_argument('device', action='store', help='Path to iBus USB interface (Bought from reslers.de)')
  return parser

def restart():
  args = sys.argv[:]
  logging.info('Re-spawning %s' % ' '.join(args))

  args.insert(0, sys.executable)

  os.chdir(_startup_cwd)
  os.execv(sys.executable, args)

#####################################
# MAIN
#####################################
parser   = createParser()
results  = parser.parse_args()
loglevel = results.verbose

signal.signal(signal.SIGINT, signal_handler_quit) # Manage Ctrl+C
configureLogging(loglevel)

devPath = sys.argv[1]
core.DEVPATH=devPath
while True:
  try:
    core.initialize()
    core.run()
  except Exception:
    logging.error("Caught unexpected exception:")
    logging.error(traceback.format_exc())
    logging.info("Going to sleep 2 seconds and restart")
    time.sleep(2)
    restart()
    
sys.exit(0)
