#!/usr/bin/python

import os, sys, time, signal, json, logging
import pyBus_core as core
import traceback

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
    'FF' : {
      '7400' : 'd_shutDown'
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
      '380601' : 'd_cdChange1',
      '380602' : 'd_cdChange2',
      '380603' : 'd_cdChange3',
      '380604' : 'd_cdChange4',
      '380605' : 'd_cdChange5',
      '380606' : 'd_cdChange6',
      '380401' : 'd_cdScanForward',
      '380400' : 'd_cdScanBackard',
      '380800' : 'd_cdRandom',
      '380801' : 'd_cdRandom'
    }
  },
  '50' : {
    'C8' : {
      '01' : 'd_test'
    }
  }
}

DOOR_LOCKED = False
WRITER = None

#####################################
# FUNCTIONS
#####################################
# Set the WRITER object (the iBus interface class) to an instance passed in from the CORE module
def init(writer):
  global WRITER
  WRITER = writer

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
    logging.debug("Directive found for following packet:")
    core.displayPacket(packet)
    result = methodToCall(packet)
  else:
    logging.debug("Directive not found for following packet:")
    core.displayPacket(packet)

  return result
  
#####################################
# All directives should have a d_ prefix as we are searching GLOBALLY for function names.. so best have unique enough names

def d_shutDown(packet):
  core.pB_display.immediateText('Shutdown')
  core.turnOff()
  
def d_test(packet):
  logging.info("Running Test")
  
def d_cdChange1(packet):
  logging.info("Running Custom 1")
  core.pB_display.immediateText('Lights: OFF')
  WRITER.writeBusPacket('00','BF', ['76', '00'])

def d_cdChange2(packet):
  logging.info("Running Custom 2")
  core.pB_display.immediateText('Lights: On')
  WRITER.writeBusPacket('00', 'BF', ['76', '11'])

def d_cdChange3(packet):
  logging.info("Running Custom 3")
  core.pB_display.immediateText('Custom')
  customPacket = '/tmp/customCommand'
  if os.path.exists(customPacket):
    try:
      pktFile = open(customPacket)
      pkt = json.loads(pktFile.read())
      pktFile.close()
      WRITER.writeBusPacket(pkt['src'], pkt['dst'], pkt['data'])
    except:
      logging.debug('Error on custom command:')
      logging.error(traceback.format_exc())

def d_cdChange4(packet):
  logging.info("Running Custom 4")
  core.pB_display.immediateText('UPDATE')
  core.pB_audio.update()
  core.pB_audio.addAll()

def d_cdChange5(packet):
  logging.info("Running Custom 5")

def d_cdChange6(packet):
  logging.info("Running Custom 6")

# This packet is used to parse all messages from the IKE (instrument control electronics), as it contains speed/RPM info. But the data for speed/rpm will vary, so it must be parsed via a method linked to 'ALL' data in the JSON DIRECTIVES
def d_custom_IKE(packet):
  packet_data = packet['dat']
  if packet_data[0] == '18':
    speed = int(packet_data[1], 16) * 2
    revs = int(packet_data[2], 16)
    customState = {'speed' : speed, 'revs' : revs}
    core.writeDataToSocket(customState) # This data is written to a file for the web-interface to display
    speedTrigger(speed) # This is a silly little thing for changing track based on speed ;)

def _displayTrackInfo(text=True):
  infoQue = []
  textQue = []
  if text:
    textQue = _getTrackTextQue()
  infoQue = _getTrackInfoQue()
  core.pB_display.setQue(textQue + infoQue)

def _getTrackInfoQue():
  displayQue = []
  status = core.pB_audio.getInfo()
  if ('status' in status):
    mpdStatus = status['status']
    if ('song' in mpdStatus and 'playlistlength' in mpdStatus):
      displayQue.append("%s of %s" % (int(mpdStatus['song'])+1, mpdStatus['playlistlength']))
  return displayQue    

def writeCurrentTrack():
  cdSongHundreds, cdSong = _getTrackNumber()
  WRITER.writeBusPacket('18', '68', ['39', '02', '09', '00', '3F', '00', cdSongHundreds, cdSong])

def _getTrackNumber():
  status = core.pB_audio.getInfo()
  cdSongHundreds = 0
  cdSong = 0
  if ('status' in status):
    mpdStatus = status['status']
    if ('song' in mpdStatus and 'playlistlength' in mpdStatus):
      cdSong = (int(mpdStatus['song'])+1) % 100
      cdSongHundreds = int(int(mpdStatus['song']) / 100)
  return cdSongHundreds, cdSong    

def _getTrackTextQue():
  displayQue = []
  status = core.pB_audio.getInfo()
  if ('track' in status):
    trackStatus = status['track']
    if ('artist' in trackStatus):
      displayQue.append(status['track']['artist'])
    if ('title' in trackStatus):
      displayQue.append(status['track']['title'])
  return displayQue

# NEXT command is invoked from the Radio. 
def d_cdNext(packet):
  core.pB_audio.next()
  writeCurrentTrack()
  _displayTrackInfo()

def d_cdPrev(packet):
  core.pB_audio.previous()
  writeCurrentTrack()
  _displayTrackInfo()

def d_cdScanForward(packet):
  cdSongHundreds, cdSong = _getTrackNumber()
  WRITER.writeBusPacket('18', '68', ['39', '03', '09', '00', '3F', '00', cdSongHundreds, cdSong])
  core.pB_audio.seek(2)

def d_cdScanBackard(packet):
  cdSongHundreds, cdSong = _getTrackNumber()
  WRITER.writeBusPacket('18', '68', ['39', '04', '09', '00', '3F', '00', cdSongHundreds, cdSong])
  core.pB_audio.seek(-2)

def d_cdStopPlaying(packet):
  core.pB_audio.pause()
  core.pB_display.setDisplay(False)
  cdSongHundreds, cdSong = _getTrackNumber()
  WRITER.writeBusPacket('18', '68', ['39', '00', '02', '00', '3F', '00', cdSongHundreds, cdSong])
  
def d_cdStartPlaying(packet):
  core.pB_audio.play()
  core.pB_display.setDisplay(True)
  writeCurrentTrack()
  _displayTrackInfo()
  
def d_cdSendStatus(packet):
  writeCurrentTrack()
  _displayTrackInfo

def d_cdPollResponse(packet):
  core.REGISTERED = True
  WRITER.writeBusPacket('18', 'FF', ['02','00'])
  
def d_cdRandom(packet):
  packet_data = packet['dat']
  random = core.pB_audio.random(0, True)
  if random:
    core.pB_display.immediateText('Random: ON')
  else:
    core.pB_display.immediateText('Random: OFF')
  _displayTrackInfo(False)
   
def speedTrigger(speed):
  global DOOR_LOCKED
  if (speed > 100):
    fastSong = "Queen/Bohemian rhaposdy.mp3"
    try:
      if (core.pB_audio.getInfoByPath(fastSong)['id'] != core.pB_audio.getTrackID()):
        core.pB_audio.addSong(fastSong)
        core.pB_audio.playSong(fastSong)
        core.pB_audio.seek(183)
        core.pB_display.immediateText('SCARAMUSCH!')
        WRITER.writeBusPacket('3F','00', ['0C', '52', '01'])
        WRITER.writeBusPacket('3F','00', ['0C', '41', '01'])
        WRITER.writeBusPacket('3F','00', ['0C', '54', '01'])
        WRITER.writeBusPacket('3F','00', ['0C', '44', '01'])

    except:
      logging.warning("Exception changing track")
  if (speed > 5):
    if not DOOR_LOCKED:
      DOOR_LOCKED = True
      WRITER.writeBusPacket('3F', '00', ['0C', '34', '01'])
      logging.debug("Set DOOR_LOCKED True")
  if (speed < 5):
    if DOOR_LOCKED:
      DOOR_LOCKED = False
      WRITER.writeBusPacket('3F', '00', ['0C', '03', '01'])
      logging.debug("Set DOOR_LOCKED False")