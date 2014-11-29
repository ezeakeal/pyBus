#!/usr/bin/python

import os
import sys
import time
import json
import signal
import logging
import binascii
import subprocess
from time import strftime as date

sys.path.append( './lib/' )

# Here we import the two types of drivers. The event driven driver, and the ticking driver.
import pyBus_eventDriver as pB_eDriver # For responding to signals

from pyBus_interface import *
#####################################
# GLOBALS
#####################################
DEVPATH           = "/dev/ttyUSB0" # This is a default, but its always overridden. So not really a default.
IBUS              = None
REGISTERED        = False # This is a temporary measure until state driven behaviour is implemented

#####################################
# FUNCTIONS

# Initializes modules as required and opens files for writing
def initialize():
  global IBUS, REGISTERED, DEVPATH
  REGISTERED=False
  
  # Initialize the iBus interface or wait for it to become available.
  while IBUS == None:
    if os.path.exists(DEVPATH):
      IBUS = ibusFace(DEVPATH)
    else:
      logging.warning("USB interface not found at (%s). Waiting 1 seconds.", DEVPATH)
      time.sleep(2)
  IBUS.waitClearBus() # Wait for the iBus to clear, then send some initialization signals
  
  pB_eDriver.init(IBUS)
  
# close the USB device and whatever else is required
def shutdown():
  global IBUS
  logging.info("Shutting down event driver")
  pB_eDriver.shutDown()
  
  if IBUS:
    logging.info("Killing iBUS instance")
    IBUS.close()
    IBUS = None

def run():
  pB_eDriver.listen()
