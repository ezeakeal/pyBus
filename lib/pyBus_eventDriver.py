#!/usr/bin/python

import os, sys, time, signal, json, logging, traceback
try:
  import alsaaudio
except:
  logging.warning("Exception importing alsaaudio")

import threading

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
      '380700' : 'd_cdScanForward',
      '380701' : 'd_cdScanBackard',
      '380601' : 'd_toggleSS', # 1 pressed
      '380602' : 'd_togglePause', # 2 pressed
      '380603' : 'd_subWDown', # 3 pressed
      '380604' : 'd_subWUp', # 4 pressed
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
      '01' : 'd_cdPollResponse', # This can happen via RT button or ignition
      '3B40' : 'd_RESET'
    }
  }
}

WRITER = None
SESSION_DATA = {}
TICK = 0.01 # sleep interval in seconds used between iBUS reads
SUB_OUT = None
#####################################
# FUNCTIONS
#####################################
# Set the WRITER object (the iBus interface class) to an instance passed in from the CORE module
def init(writer):
  global WRITER, SESSION_DATA, SUB_OUT
  WRITER = writer

  try:
    SUB_OUT = alsaaudio.Mixer("PCM") # I have output sent to two devices in MPD - HW index 0 is the default sound device, which is plugged in to my sub in the boot.
  except Exception, e:
    logging.warning("Exception opening Sub audio output")
    print e

  pB_display.init(WRITER)
  pB_audio.init()
  pB_ticker.init(WRITER)
  
  WRITER.writeBusPacket('18', 'FF', ['02', '01'])

  SESSION_DATA["DOOR_LOCKED"] = False
  SESSION_DATA["SPEED_SWITCH"] = False

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
      result = methodToCall(packet)
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
  
  if SESSION_DATA['DOOR_LOCKED']:
    SESSION_DATA['DOOR_LOCKED'] = False
    WRITER.writeBusPacket('3F', '00', ['0C', '03', '01']) # Unlock the door

  WRITER.writeBusPacket('3F','00', ['0C', '53', '01']) # Put up window 1
  WRITER.writeBusPacket('3F','00', ['0C', '42', '01']) # Put up window 2
  WRITER.writeBusPacket('3F','00', ['0C', '55', '01']) # Put up window 3
  WRITER.writeBusPacket('3F','00', ['0C', '43', '01']) # Put up window 4
  
def d_toggleSS(packet):
  global SESSION_DATA
  logging.info("Running Custom 1")
  SESSION_DATA['SPEED_SWITCH'] = not SESSION_DATA['SPEED_SWITCH']
  if SESSION_DATA['SPEED_SWITCH']:
    pB_display.immediateText('SpeedSw: On')
  else: 
    pB_display.immediateText('SpeedSw: Off')

def d_togglePause(packet):
  logging.info("Play/Pause")
  status = pB_audio.getInfo()
  if (status['status']['state'] != "play"):
    pB_display.immediateText('Play')
    pB_audio.play()
  else:
    pB_display.immediateText('Pause')
    pB_audio.pause()
  
def d_update(packet):
  # TODO Implement a status updater using the tickUtil
  logging.info("UPDATE")
  pB_display.immediateText('UPDATING')
  pB_audio.update()
  pB_audio.addAll()
  
def d_RESET(packet):
  logging.info("RESET")
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
  pB_audio.next()
  writeCurrentTrack()
  _displayTrackInfo()

def d_cdPrev(packet):
  pB_audio.previous()
  writeCurrentTrack()
  _displayTrackInfo()

def d_cdScanForward(packet):
  cdSongHundreds, cdSong = _getTrackNumber()
  WRITER.writeBusPacket('18', '68', ['39', '03', '09', '00', '3F', '00', cdSongHundreds, cdSong])
  if "".join(packet['dat']) == "380400":
    WRITER.writeBusPacket('18', '68', ['39', '03', '09', '00', '3F', '00', cdSongHundreds, cdSong]) # Fast forward scan signal
    pB_ticker.enableFunc("scanForward", 0.1)

def d_cdScanBackard(packet):
  cdSongHundreds, cdSong = _getTrackNumber()
  WRITER.writeBusPacket('18', '68', ['39', '04', '09', '00', '3F', '00', cdSongHundreds, cdSong]) # Fast backward scan signal
  if "".join(packet['dat']) == "380401":
    pB_ticker.enableFunc("scanBackward", 0.1)

# Stop playing, turn off display writing
def d_cdStopPlaying(packet):
  pB_audio.pause()
  pB_display.setDisplay(False)
  cdSongHundreds, cdSong = _getTrackNumber()
  WRITER.writeBusPacket('18', '68', ['39', '00', '02', '00', '3F', '00', cdSongHundreds, cdSong])
  
# Start playing, turn on display writing
def d_cdStartPlaying(packet):
  pB_audio.play()
  pB_display.setDisplay(True)
  pB_ticker.disableAllFunc()
  writeCurrentTrack()
  _displayTrackInfo()

# Unsure..  
def d_cdSendStatus(packet):
  writeCurrentTrack()
  _displayTrackInfo

# Respond to the Poll for changer alive
def d_cdPollResponse(packet):
  pB_ticker.disableFunc("pollResponse")
  pB_ticker.enableFunc("pollResponse", 30)
  
# Enable/Disable Random
def d_cdRandom(packet):
  packet_data = packet['dat']
  random = pB_audio.random(0, True)
  if random:
    pB_display.immediateText('Random: ON')
  else:
    pB_display.immediateText('Random: OFF')
  _displayTrackInfo(False)
   
def d_subWDown(packet):
  if SUB_OUT:
    setVol = max(SUB_OUT.getvolume()[0] - 10, 50) # 50 is lower limit, as that will be the max in worst scenarios
    SUB_OUT.setvolume(setVol)
    pB_display.immediateText("Sub Down (%s)" % setVol)

def d_subWUp(packet):
  if SUB_OUT:
    setVol = min(SUB_OUT.getvolume()[0] + 10, 100) # 100 is upper limit, as that will be the lower in worst scenarios
    SUB_OUT.setvolume(setVol)
    pB_display.immediateText("Sub Up (%s)" % setVol)

# Do whatever you like here regarding the speed!
def speedTrigger(speed):
  global SESSION_DATA
  if (speed > 100) and SESSION_DATA['SPEED_SWITCH']:
    try:
        pB_display.immediateText('WINDOWS!')
        WRITER.writeBusPacket('3F','00', ['0C', '52', '01'])
        WRITER.writeBusPacket('3F','00', ['0C', '41', '01'])
        WRITER.writeBusPacket('3F','00', ['0C', '54', '01'])
        WRITER.writeBusPacket('3F','00', ['0C', '44', '01'])
    except:
      logging.warning("Exception in speed trigger")
      
  if (speed > 5):
    if not SESSION_DATA['DOOR_LOCKED']:
      SESSION_DATA['DOOR_LOCKED'] = True
      WRITER.writeBusPacket('3F', '00', ['0C', '34', '01'])

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
