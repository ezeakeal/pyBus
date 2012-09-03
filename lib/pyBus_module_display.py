#!/usr/bin/python

import os, sys, time, signal, json, traceback, logging
import threading
import pyBus_core as core
import datetime

#####################################
# WARNING: Behaviour of this module is going to be rebuilt entirely, it is moving towards spaghetti code.
#####################################

#####################################
# GLOBALS
#####################################

DISPLAY_QUE = []
TICK = 1 # sleep interval in seconds used after displaying a string from DISPLAY_QUE
WRITER = None # Writer thread
DISPLAY_TEXT = True # whether or not to allow the module to write to display (Note, immediateText() does not care about this)
MAX_STRINGLEN = 10 # max characters we can fit on display

#####################################
# FUNCTIONS
#####################################
# Convert text to hex and prepends the required data for displaying text on the Radio
def _hexText(string):
  dataPacket = ['23', '42', '01']
  stringLen = 0
  while (stringLen < MAX_STRINGLEN) and (len(string) > 0):
    c = string[stringLen] # stringLen doubles up as the index to use when retrieving characters of the string to be displayed.. apologies for how misleading this may be
    dataPacket.append('%02X' % (ord(c)))
    stringLen = stringLen + 1
    if (stringLen == len(string)):
      break
  return dataPacket

# Sets the string that should be displayed/scrolled
# If the string being set differs from the current string, set the display offset to 0
def addStringToQue(string):
  global DISPLAY_QUE
  DISPLAY_QUE.append(string)
  
# Increment display offset to scroll screen. Once scrolled, set to next display mode
def _scrollDisplay():
  global DISPLAY_QUE
  string = DISPLAY_QUE[0]
  if (len(string) > MAX_STRINGLEN):
    string = string[1:30] # if you have more than 30 characters you can go suck a lemon, scrolling text is already hogging a lot of the bus
  insertStringToQue(string, 1) # insert it after this string as this element will be deleted in the updateQue method

def insertStringToQue(string, pos=0):
  global DISPLAY_QUE
  DISPLAY_QUE.insert(pos, string)

def immediateText(string):
  insertStringToQue(string)
  WRITER.write()
  updateQue()

def updateQue():
  global DISPLAY_QUE
  if (len(DISPLAY_QUE) > 0):
    del DISPLAY_QUE[0]

def setQue(que):
  global DISPLAY_QUE
  DISPLAY_QUE = que
  
def setDisplay(safe):
  global DISPLAY_TEXT
  DISPLAY_TEXT = safe

#------------------------------------
# THREAD FOR TICKING AND WRITING
#------------------------------------
class busWriter ( threading.Thread ):
  def __init__ ( self, ibus ):
    self.IBUS = ibus
    threading.Thread.__init__ ( self )

  def write(self):
    if (len(DISPLAY_QUE) > 0):
      string = DISPLAY_QUE[0]
      self.IBUS.writeBusPacket('C8', '80', _hexText(string)) 
  
  def run(self):
    logging.info('Display thread initialized')
    while True:
      if DISPLAY_TEXT:
        busWriter.write(self) # write
        scrollDisplay() # scroll text if required
        updateQue() # removes the element that we just printed
      time.sleep(TICK) # sleep a bit

  def stop(self):
    self.IBUS = None
    self._Thread__stop()
#------------------------------------

def init(IBUS):
  global WRITER
  WRITER = busWriter(IBUS)
  WRITER.start()

def end():
  if WRITER:
    WRITER.stop()