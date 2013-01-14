#!/usr/bin/python

import os, sys, time, signal, json, logging, traceback
import threading

import pyBus_module_display as pB_display # Only events can manipulate the display stack
import pyBus_module_audio as pB_audio # Add the audio module as it will only be manipulated from here in pyBus

# This module will read a packet, match it against the json object 'DIRECTIVES' below. 
# The packet is checked by matching the source value in packet (i.e. where the packet came from) to a key in the object if possible
# Then matching the Destination if possible
# The joining the 'data' component of the packet and matching that if possible.
# The resulting value will be the name of a function to pass the packet to for processing of sorts.

# THE MAJOR DIFFRENCE BETWEEN THIS DRIVER AND EVENT DRIVER:
# This one should manipulate the state data object and use that with
# a ticking thread to figure out what to do. So tick every .5 sec or 
# so and perform an action depending on the state data like skipping
# back or forward.

#####################################
# GLOBALS
#####################################
# directives list - maps function to src:dest:data
# first level of directives is filtering the src, so put in the integer representation of the src
# second level is destination
# third level is data : function name
DIRECTIVES = {
  '44' : {
    'BF' : {
      '7401FF' : 'd_keyOut'
    }
  },
  '80' : {
    'BF' : {
      'ALL' : 'd_custom_IKE' # Use ALL to send all data to a particular function
    }
  },
  '68' : {
    '18' : {
      '01'     : 'd_cdPollResponse',
      '380000' : 'd_cdSendStatus',
      '380100' : 'd_cdStopPlaying',
      '380300' : 'd_cdStartPlaying',
      '380A00' : 'd_cdNext',
      '380A01' : 'd_cdPrev',
      '380700' : 'd_cdScanForward',
      '380701' : 'd_cdScanBackard',
      '380601' : 'd_toggleSS', # 1 pressed
      '380602' : 'd_togglePause', # 2 pressed
      '380603' : 'd_cdChange3', # 3 pressed
      '380604' : 'd_cdChange4', # 4 pressed
      '380605' : 'd_update', # 5 pressed
      '380606' : 'd_RESET', # 6 pressed
      '380401' : 'd_cdScanForward',
      '380400' : 'd_cdScanBackard',
      '380800' : 'd_cdRandom',
      '380801' : 'd_cdRandom'
    }
  },
  '50' : {
    'C8' : {
      '01'   : 'd_RESET',
      '3B40' : 'd_RESET'
    }
  }
}


WRITER = None
LISTENER = None
STATE_DATA = {}
TICK = 0.01 # sleep interval in seconds used between iBUS reads

#####################################
# FUNCTIONS
#####################################
# Set the WRITER object (the iBus interface class) to an instance passed in from the CORE module
def init(writer):
  logging.info("In empty ticker")

# Manage the packet, meaning traverse the JSON 'DIRECTIVES' object and attempt to determine a suitable function to pass the packet to.
def manage(packet):
  src = packet['src']
  dst = packet['dst']
  dataString = ''.join(packet['dat'])
  methodName = None

  try:
    dstDir = DIRECTIVES[src][dst]
    if ('ALL'  in dstDir.keys()):
      methodName = dstDir['ALL']
    else:
      methodName = dstDir[dataString]
  except Exception, e:
    logging.warning(e)
    
  result = None
  if methodName != None:
    methodToCall = globals()[methodName]
    logging.debug("Directive found for packet - %s" % methodName)
    result = methodToCall(packet)
  else:
    logging.debug("Directive not found for packet")

  return result
  
def shutDown():
  LISTENER.end()
  pB_display.end()

#------------------------------------
# THREAD FOR TICKING AND WRITING
#------------------------------------
class eventDriver ( threading.Thread ):
  def __init__ ( self, ibus ):
    self.IBUS = ibus
    threading.Thread.__init__ ( self )
  
  def run(self):
    logging.info('Event listener initialized')
    while True:
      packet = self.IBUS.readBusPacket()
      if packet:
        pB_eDriver.manage(packet)
      time.sleep(TICK) # sleep a bit

  def stop(self):
    self.IBUS = None
    self._Thread__stop()
#------------------------------------

class TriggerRestart(Exception):
  pass
class TriggerInit(Exception):
  pass
