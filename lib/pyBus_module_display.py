#!/usr/bin/python

import os, sys, time, signal, json, traceback
import threading
import pyBus_core as core
import datetime

#####################################
# WARNING: Behaviour of this module is going to be rebuilt entirely, it is moving towards spaghetti code.
#####################################

#####################################
# GLOBALS
#####################################

DISPLAY_STR = "" # Initial display string
DISPLAY_OFFSET = 0 # Offset for moving string
DISPLAY_WIDTH = 12 # Length of display unit in characters
MODE = "" # Mode, used to determine how to set the display_str
MODE_NEXT = "" 
TICK = 0.5 # sleep time in seconds for iBus write loop

WRITER = None
#####################################
# FUNCTIONS
#####################################
# Convert text to hex and prepends the required data
def hexText(string):
  dataPacket = ['23', '42', '01']
  string = string[DISPLAY_OFFSET:DISPLAY_OFFSET+DISPLAY_WIDTH]
  for c in string:
    dataPacket.append('%02X' % (ord(c)))
  return dataPacket

# Sets the string that should be displayed/scrolled
# If the string being set differs from the current string, set the display offset to 0
def setString(string):
  global DISPLAY_STR, DISPLAY_OFFSET
  if (string != DISPLAY_STR):
    DISPLAY_OFFSET = 0
  DISPLAY_STR = string
  
# Increment display offset to scroll screen. Once scrolled, set to next display mode
def scrollDisplay():
  global DISPLAY_OFFSET
  DISPLAY_OFFSET = DISPLAY_OFFSET + 1
  if (len(DISPLAY_STR) - DISPLAY_OFFSET <= DISPLAY_WIDTH-2): # - 2 to make it last a bit
    setMode(MODE_NEXT)

# Globally sets the display mode
def setMode(mode, next=""):
  global MODE, MODE_NEXT
  MODE = mode
  MODE_NEXT = next
  DISPLAY_OFFSET = 0

# Gets and sets the text for the display unit
def getText():
  global MODE_NEXT, TICK
  trackStr = ""
  try:
    if (MODE == "cd_track"):
      TICK=0.5
      status = core.pB_audio.getInfo()
      trackStr = "%s - %s" % (status['track']['artist'], status['track']['title'])
    elif (MODE == "cd_title"):
      trackStr = "%s" % (status['track']['title'])
      MODE_NEXT = "cd_title"
    elif (MODE == "cd_progress"):
      TICK = 1
      MODE_NEXT = 'cd_progress'
      status = core.pB_audio.getInfo()
      timeStatus = status['status']['time'].split(':')
      time_0 = str(datetime.timedelta(seconds=int(timeStatus[0])))[2:10]
      time_1 = str(datetime.timedelta(seconds=int(timeStatus[1])))[2:10]
      trackStr = "%s/%s" % (time_0, time_1)
    else:
      trackStr = MODE
  except e:
    trackStr = "ERROR"
    core.printOut(e, 2)
  setString(trackStr)

def instantText(string):
  global MODE, MODE_NEXT
  MODE_NEXT = MODE
  setMode(string) # Sets mode to the string. By default, this will set text to the mode

#------------------------------------
# THREAD FOR TICKING AND WRITING
#------------------------------------
class busWriter ( threading.Thread ):
  def __init__ ( self, writer ):
    self.writer = writer
    threading.Thread.__init__ ( self )

  def write(self):
    if (DISPLAY_STR != ""):
      self.writer.writeBusPacket('C8', '80', hexText(DISPLAY_STR)) 

  def run(self):
    core.printOut('Display writing thread initialized', 0)
    while True:
      getText() # get text
      busWriter.write(self) # write
      scrollDisplay() # scroll if required
      time.sleep(TICK) # sleep a bit

  def stop(self):
    self._Thread__stop()
#------------------------------------

def init(writer):
  global WRITER
  WRITER = busWriter(writer)
  WRITER.start()

def end():
  WRITER.stop()