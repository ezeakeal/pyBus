#!/usr/bin/python

import os
import time
import json
import random
import logging

import pyBus_module_display as pB_display # Only events can manipulate the display stack
import pyBus_module_audio as pB_audio # Add the audio module as it will only be manipulated from here in pyBus
import pyBus_tickUtil as pB_ticker # Ticker for signals requiring intervals


logger = logging.getLogger(__name__)
#####################################
# GLOBALS
#####################################
WRITER = None
SESSION_DATA = {}
TICK = 0.02 # sleep interval in seconds used between iBUS reads


def init(writer):
  global WRITER, SESSION_DATA
  WRITER = writer

  pB_display.init(WRITER)
  pB_audio.init()
  pB_ticker.init(WRITER)
  
  pB_ticker.enableFunc("announce", 10)

  SESSION_DATA["DOOR_LOCKED"] = False
  SESSION_DATA["SPEED_SWITCH"] = False

  pB_display.immediateText('PyBus Up')
  WRITER.writeBusPacket('3F', '00', ['0C', '4E', '01']) # Turn on the 'clown nose' for 3 seconds

  
def listen():
  logging.info('Event listener initialized')
  while True:
    packet = WRITER.readBusPacket()
    if packet:
      manage(packet)
    time.sleep(TICK) # sleep a bit

def shutDown():
  logging.debug("Quitting Audio Client")
  pB_audio.quit()
  logging.debug("Stopping Display Driver")
  pB_display.end()
  logging.debug("Killing tick utility")
  pB_ticker.shutDown()


############################################################################
# FROM HERE ON ARE THE DIRECTIVES
# DIRECTIVES ARE WHAT I CALL SMALL FUNCTIONS WHICH ARE INVOKED WHEN A 
# CERTAIN CODE IS READ FROM THE IBUS.
#
# SO ADD YOUR OWN IF YOU LIKE, OR MODIFY WHATS THERE. 
# USE THE BIG JSON DICTIONARY AT THE TOP
############################################################################
# All directives should have a d_ prefix as we are searching GLOBALLY for function names.. so best have unique enough names
############################################################################

################## DIRECTIVE UTILITY FUNCTIONS ##################
# Write current track to display 
def writeCurrentTrack():
  cdSongHundreds, cdSong = _getTrackNumber()
  WRITER.writeBusPacket('18', '68', ['39', '02', '09', '00', '3F', '00', cdSongHundreds, cdSong])

# Sets the text stack to something..
def _displayTrackInfo(text=True):
  infoQue = []
  textQue = []
  if text:
    textQue = _getTrackTextQue()
  infoQue = _getTrackInfoQue()
  pB_display.setQue(textQue + infoQue)

# Get some info text to display
def _getTrackInfoQue():
  displayQue = []
  status = pB_audio.getInfo()
  if ('status' in status):
    mpdStatus = status['status']
    if ('song' in mpdStatus and 'playlistlength' in mpdStatus):
      displayQue.append("%s of %s" % (int(mpdStatus['song'])+1, mpdStatus['playlistlength']))
  return displayQue    

# Get the current track number and hundreds.. oh god I should have documented this sooner
def _getTrackNumber():
  status = pB_audio.getInfo()
  cdSongHundreds = 0
  cdSong = 0
  if ('status' in status):
    mpdStatus = status['status']
    if ('song' in mpdStatus and 'playlistlength' in mpdStatus):
      cdSong = (int(mpdStatus['song'])+1) % 100
      cdSongHundreds = int(int(mpdStatus['song']) / 100)
  return cdSongHundreds, cdSong    

# Get the track text to put in display stack
def _getTrackTextQue():
  displayQue = []
  status = pB_audio.getInfo()
  if ('track' in status):
    trackStatus = status['track']
    if trackStatus:
      if ('artist' in trackStatus):
        displayQue.append(status['track']['artist'])
      if ('title' in trackStatus):
        displayQue.append(status['track']['title'])
    else:
      displayQue.append("Paused")
  return displayQue
#################################################################
