#!/usr/bin/python

import os, sys, time, signal, binascii, termcolor, json
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
  '44' : '?????',
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

LOGFILE_ERROR = "/var/log/dv_pybus/error.log"
LOGFILE_STDRD = "/var/log/dv_pybus/output.log"
LOG_ERROR = None
LOG_STDRD = None

PYBUS_SOCKET_FILE = '/tmp/ibus_custom.log'

WRITER = None

#####################################
# FUNCTIONS
#####################################
# This is a very hacked together solution for communicating the speed/rpm of the engine to the web-interface..
# This WILL be fixed soon.
def writeCustomData(data):
  logFile = open(PYBUS_SOCKET_FILE, 'w')
  logFile.write(json.dumps(data))
  logFile.close()

# Print the locations in english
def mapBusLocation(hexChar):
  if hexChar not in LOCATIONS.keys():
    return "UNKNOWN"
  return LOCATIONS[hexChar]

# Print coloured output based on 'state'
# Data is also written to one of two log files depending on the value of state (State > 0 writes to error log)
def printOut(text, state):
  color = "white"
  if state == 0:
    color = "green"
    textType = "OK"
  if state == 1:
    color = "yellow"
    textType = "WARN"
  if state == 2:
    color = "red"
    textType = "ERROR"
  if state == 3:
    color = "blue"
    textType = "INFO"
  
  timeStamp = date('%Y-%m-%d %H:%M:%S')
  if (LOG_STDRD and LOG_ERROR):
    logText = '%s [%s] %s\n' % (timeStamp, textType, text)
    if state == 0:
      LOG_STDRD.write(logText)
    else:
      LOG_ERROR.write(logText)
  termcolor.cprint(text, color)

  
# Print out the packet received in a nice way.. everyone is happy
def displayPacket(packet, status):
  srcText = mapBusLocation(packet['src'])
  lenText = int(packet['len'], 16)
  dstText = mapBusLocation(packet['dst'])
  printOut("-------PACKET-------", status)
  printOut("Source: (%s) %s" % (packet['src'], srcText), status)
  printOut("Destination: (%s) %s" % (packet['dst'], dstText), status)
  printOut("Length: %s" % lenText, status)
  printOut("Data: %s" % packet['dat'], status)
  printOut("", status)
  
# Never ending loop to read the packets on the bus, which may possibly be responded to via the directives module
def readBusLoop():
  while True:
    packet = WRITER.readBusPacket()
    directives.manage(packet)

# A small function to send signals during initialization if required, currently this registers pyBus as a CD-Changer on the iBus. 
# This will be replaced by a separate thread which will monitor the state of signals and change behaviour accordingly 
def initSignals():
  print "Sending initialize signals"
  WRITER.writeBusPacket('18', 'FF', ['02', '01'])

# Initializes modules as required and opens files for writing
def initialize(devPath):
  global WRITER, LOG_ERROR, LOG_STDRD
  LOG_ERROR = open(LOGFILE_ERROR, 'a')
  LOG_STDRD = open(LOGFILE_STDRD, 'a')
  WRITER = ibusFace(devPath)
  pB_audio.init()
  # pB_display.init(WRITER)
  directives.init(WRITER)
  # Wait for the iBus to clear, then send some initialization signals
  WRITER.waitClearBus()
  initSignals()

# close the USB device and whatever else is required
def shutdown():
  pB_display.end()
  WRITER.close()
  LOG_ERROR.close()
  LOG_STDRD.close()
  pB_audio.stop()

def run():
  readBusLoop()