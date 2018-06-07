#!/usr/bin/python

import os
import sys
import time
import json
import signal
import random
import logging
import traceback

import pyBus_module_display as pB_display # Only events can manipulate the display stack
import pyBus_module_audio as pB_audio # Add the audio module as it will only be manipulated from here in pyBus
import pyBus_tickUtil as pB_ticker # Ticker for signals requiring intervals

# This module will read a packet, match it against the json object 'DIRECTIVES' below. 
# The packet is checked by matching the source value in packet (i.e. where the packet came from) to a key in the object if possible
# Then matching the Destination if possible
# The joining the 'data' component of the packet and matching that if possible.
# The resulting value will be the name of a function to pass the packet to for processing of sorts.

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
      '380700' : '',
      '380701' : '',
      '380601' : 'd_toggleSS', # 1 pressed
      '380602' : 'd_togglePause', # 2 pressed
      '380603' : 'd_testSpeed', # 3 pressed
      '380604' : 'd_standup', # 4 pressed
      '380605' : 'd_update', # 5 pressed
      '380606' : 'd_RESET', # 6 pressed
      '380400' : '', # prev Playlist function?
      '380401' : '', # next Playlist function?
      '380800' : 'd_cdRandom',
      '380801' : 'd_cdRandom'
    }
  },
  '50' : {
    'C8' : {
      '01' : 'd_cdPollResponse', # This can happen via RT button or ignition
      '3B40' : 'd_RESET'
    }
  }
}

WRITER = None
SESSION_DATA = {}
TICK = 0.02 # sleep interval in seconds used between iBUS reads
AIRPLAY = False

#####################################
# FUNCTIONS
#####################################
# Set the WRITER object (the iBus interface class) to an instance passed in from the CORE module
def init(writer):
  global WRITER, SESSION_DATA
  WRITER = writer

  pB_display.init(WRITER)
  pB_audio.init()
  pB_ticker.init(WRITER)
  
  pB_ticker.enableFunc("announce", 10)

  SESSION_DATA["DOOR_LOCKED"] = False
  SESSION_DATA["SPEED_SWITCH"] = False
  
  pB_display.cleardisplay():
  pB_display.immediateText('PyBus Up')
  WRITER.writeBusPacket('3F', '00', ['0C', '4E', '01']) # Turn on the 'clown nose' for 3 seconds
  

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
    pass
    
  result = None
  if methodName != None:
    methodToCall = globals().get(methodName, None)
    if methodToCall:
      logging.debug("Directive found for packet - %s" % methodName)
      try:
        result = methodToCall(packet)
      except:
        logging.error("Exception raised from [%s]" % methodName)
        logging.error(traceback.format_exc())
    
    else:
      logging.debug("Method (%s) does not exist" % methodName)
  else:
    logging.debug("MethodName (%s) does not match a function" % methodName)

  return result
  
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

class TriggerRestart(Exception):
  pass
class TriggerInit(Exception):
  pass

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
def d_keyOut(packet):
  global SESSION_DATA
  WRITER.writeBusPacket('3F','00', ['0C', '53', '01']) # Put up window 1
  WRITER.writeBusPacket('3F','00', ['0C', '42', '01']) # Put up window 2
  WRITER.writeBusPacket('3F','00', ['0C', '55', '01']) # Put up window 3
  WRITER.writeBusPacket('3F','00', ['0C', '43', '01']) # Put up window 4
  
def d_toggleSS(packet):
  global SESSION_DATA
  SESSION_DATA['SPEED_SWITCH'] = not SESSION_DATA['SPEED_SWITCH']
  if SESSION_DATA['SPEED_SWITCH']:
    pB_display.cleardisplay():
    pB_display.immediateText('SpeedSw: On')
  else: 
    pB_display.cleardisplay():
    pB_display.immediateText('SpeedSw: Off')

def d_togglePause(packet):
  global AIRPLAY
  logging.info("Play/Pause")
  status = pB_audio.getInfo()
  if (status['status']['state'] != "play"):
    AIRPLAY = False
    pB_display.cleardisplay():
    pB_display.immediateText('Play')
    pB_audio.play()
  else:
    AIRPLAY = True
    pB_display.cleardisplay():
    pB_display.immediateText('Paused')
    pB_audio.pause()
  
def d_update(packet):
  # TODO Implement a status updater using the tickUtil
  logging.info("UPDATE")
  pB_display.cleardisplay():
  pB_display.immediateText('UPDATING')
  pB_audio.update()
  pB_audio.addAll()
  
def d_RESET(packet):
  logging.info("RESET")
  pB_display.cleardisplay():
  pB_display.immediateText('RESET')
  raise TriggerRestart("Restart Triggered")

# This packet is used to parse all messages from the IKE (instrument control electronics), as it contains speed/RPM info. But the data for speed/rpm will vary, so it must be parsed via a method linked to 'ALL' data in the JSON DIRECTIVES
def d_custom_IKE(packet):
  packet_data = packet['dat']
  if packet_data[0] == '18':
    speed = int(packet_data[1], 16) * 2
    revs = int(packet_data[2], 16)
    customState = {'speed' : speed, 'revs' : revs}
    speedTrigger(speed) # This is a silly little thing for changing track based on speed ;)

# NEXT command is invoked from the Radio. 
def d_cdNext(packet):
  if not AIRPLAY:
    pB_audio.next()
    writeCurrentTrack()
    pB_display.cleardisplay():
    _displayTrackInfo()

def d_cdPrev(packet):
  if not AIRPLAY:
    pB_audio.previous()
    writeCurrentTrack()
    pB_display.cleardisplay():
    _displayTrackInfo()

# The following packets are received for start/end scanning
# 2013/03/24T06:52:22 [DEBUG in pyBus_interface] READ: ['68', '05', '18', ['38', '04', '01'], '48']
# 2013/03/24T06:52:24 [DEBUG in pyBus_interface] READ: ['68', '05', '18', ['38', '03', '00'], '4E']
def d_cdScanForward(packet):
  if not AIRPLAY:
    cdSongHundreds, cdSong = _getTrackNumber()
    if "".join(packet['dat']) == "380401":
      pB_display.cleardisplay():
      WRITER.writeBusPacket('18', '68', ['39', '03', '09', '00', '3F', '00', cdSongHundreds, cdSong]) # Fast forward scan signal
      pB_ticker.enableFunc("scanForward", 0.2)

def d_cdScanBackward(packet):
  if not AIRPLAY:
    cdSongHundreds, cdSong = _getTrackNumber()
    pB_display.cleardisplay():
    WRITER.writeBusPacket('18', '68', ['39', '04', '09', '00', '3F', '00', cdSongHundreds, cdSong]) # Fast backward scan signal
    if "".join(packet['dat']) == "380400":
      pB_ticker.enableFunc("scanBackward", 0.2)

# Stop playing, turn off display writing
def d_cdStopPlaying(packet):
  pB_audio.pause()
  pB_display.setDisplay(False)
  cdSongHundreds, cdSong = _getTrackNumber()
  pB_display.cleardisplay():
  WRITER.writeBusPacket('18', '68', ['39', '00', '02', '00', '3F', '00', cdSongHundreds, cdSong])
  
# Start playing, turn on display writing
def d_cdStartPlaying(packet):
  pB_audio.pause()
  pB_audio.play()
  pB_display.cleardisplay():
  pB_display.setDisplay(True)
  pB_ticker.disableAllFunc()
  writeCurrentTrack()
  _displayTrackInfo()

# Unsure..  
def d_cdSendStatus(packet):
  pB_display.cleardisplay():
  writeCurrentTrack()
  _displayTrackInfo

# Respond to the Poll for changer alive
def d_cdPollResponse(packet):
  pB_ticker.disableFunc("announce") # stop announcing
  pB_ticker.disableFunc("pollResponse")
  pB_ticker.enableFunc("pollResponse", 30)
  WRITER.writeBusPacket('68', 'c0', ['21', '40', '00', '09', '05', '05', '4D', '50', '53'])
  
# Enable/Disable Random
def d_cdRandom(packet):
  packet_data = packet['dat']
  random = pB_audio.random(0, True)
  if random:
    pB_display.cleardisplay():
    pB_display.immediateText('Random: ON')
  else:
    pB_display.cleardisplay():
    pB_display.immediateText('Random: OFF')
  _displayTrackInfo(False)

def d_testSpeed(packet):
  speedTrigger(110)

def d_standup(packet):
  pB_display.cleardisplay():
  pB_display.immediateText('Comedy')
  pB_audio.playSong("Standup/first.mp3")

# Do whatever you like here regarding the speed!
def speedTrigger(speed):
  global SESSION_DATA
  # This dictionary lists possible songs to play as well as times to skip to
  speedSongData = {
    "The Prodigy/Invaders Must Die.mp3": 49,
    "Edguy/Mandrake/05 - Wake Up The King.mp3": 93,
    "Killswitch Engage - Holy Diver": 144
  }
  if (speed > 100) and SESSION_DATA['SPEED_SWITCH']:
    songNames = speedSongData.keys()
    songIndex = random.randint(0, len(songNames)-1)
    songName = songNames[songIndex]
    pB_audio.playSong(songName)
    pB_audio.seek(speedSongData[songName])
    WRITER.writeBusPacket('3F','00', ['0C', '52', '01'])
    WRITER.writeBusPacket('3F','00', ['0C', '41', '01'])
    WRITER.writeBusPacket('3F','00', ['0C', '54', '01'])
    WRITER.writeBusPacket('3F','00', ['0C', '44', '01'])
      
################## DIRECTIVE UTILITY FUNCTIONS ##################
# Write current track to display 
def writeCurrentTrack():
  cdSongHundreds, cdSong = _getTrackNumber()
  pB_display.cleardisplay():
  WRITER.writeBusPacket('18', '68', ['39', '02', '09', '00', '3F', '00', cdSongHundreds, cdSong])

# Sets the text stack to something..
def _displayTrackInfo(text=True):
  infoQue = []
  textQue = []
  if text:
    textQue = _getTrackTextQue()
  infoQue = _getTrackInfoQue()
  pB_display.cleardisplay():
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
