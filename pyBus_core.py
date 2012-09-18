#!/usr/bin/python

import os, sys, time, signal, binascii, termcolor, json, logging, subprocess
from time import strftime as date

sys.path.append( './lib/' )

import pyBus_directives as directives
import pyBus_module_audio as pB_audio
import pyBus_module_display as pB_display
from pyBus_interface import *
#####################################
# GLOBALS
#####################################
# LOCATIONS, a mapping of hex codes seen in SRC/DST parts of packets. This WILL change across models/years.

LOCATIONS = {
  '00' : 'Broadcast',
  '18' : 'CDW - CDC CD-Player',
  '30' : '?????',
  '3B' : 'NAV Navigation/Videomodule',
  '43' : 'MenuScreen',
  '44' : 'Ignition?',
  '50' : 'MFL Multi Functional Steering Wheel Buttons',
  '60' : 'PDC Park Distance Control',
  '68' : 'RAD Radio',
  '6A' : 'DSP Digital Sound Processor',
  '7F' : '?????',
  '80' : 'IKE Instrument Control Electronics',
  'BF' : 'BROADCAST LCM?',
  'C0' : 'MID Multi-Information Display Buttons',
  'C8' : 'TEL Telephone',
  'D0' : 'Navigation Location',
  'E7' : 'OBC TextBar',
  'E8' : '?????',
  'ED' : 'Lights, Wipers, Seat Memory',
  'F0' : 'BMB Board Monitor Buttons',
  'FF' : 'Broadcast'
}

DEVPATH           = "/dev/ttyUSB0"
LOGFILE           = "/music/pyBus/pybus.log"
PYBUS_SOCKET_FILE = '/tmp/ibus_custom.log'
IBUS              = None
REGISTERED        = False # This is a temporary measure until state driven behaviour is implemented

#####################################
# FUNCTIONS
#####################################
# This is a very hacked together solution for communicating the speed/rpm of the engine to the web-interface..
# This WILL be fixed soon.
def writeDataToSocket(data):
  logFile = open(PYBUS_SOCKET_FILE, 'w')
  logFile.write(json.dumps(data))
  logFile.close()

# Print the locations in english
def mapBusLocation(hexChar):
  if hexChar not in LOCATIONS.keys():
    return "UNKNOWN"
  return LOCATIONS[hexChar]
  
# Print out the packet received in a nice way.. everyone is happy
def displayPacket(packet):
  srcText = mapBusLocation(packet['src'])
  lenText = int(packet['len'], 16)
  dstText = mapBusLocation(packet['dst'])
  logging.debug("-------PACKET-------")
  logging.debug("Source: (%s) %s", packet['src'], srcText)
  logging.debug("Destination: (%s) %s", packet['dst'], dstText)
  logging.debug("Length: %s", lenText)
  logging.debug("Data: %s", packet['dat'])
  
# Never ending loop to read the packets on the bus, which may possibly be responded to via the directives module
def readBusLoop():
  while True:
    packet = IBUS.readBusPacket()
    if packet:
      directives.manage(packet)

# A small function to send signals during initialization if required, currently this registers pyBus as a CD-Changer on the iBus. 
# This will be replaced by a separate thread which will monitor the state of signals and change behaviour accordingly 
def initSignals():
  IBUS.writeBusPacket('18', 'FF', ['02', '01'])

# Initializes modules as required and opens files for writing
def initialize():
  global IBUS, REGISTERED, DEVPATH
  REGISTERED=False
  # Initialize the iBus interface
  while IBUS == None:
    if os.path.exists(DEVPATH):
      IBUS = ibusFace(DEVPATH)
    else:
      logging.warning("USB interface not found at (%s). Waiting 2 seconds.", DEVPATH)
      time.sleep(2)
  pB_audio.init()
  pB_display.init(IBUS)
  directives.init(IBUS)
  IBUS.waitClearBus() # Wait for the iBus to clear, then send some initialization signals
  initSignals()
  pB_display.immediateText('PyBus Up')
  IBUS.writeBusPacket('3F', '00', ['0C', '4E', '01'])

# close the USB device and whatever else is required
def shutdown():
  pB_display.end()
  if IBUS:
    IBUS.close()
    IBUS = None
  pB_audio.stop()

def run():
  readBusLoop()
