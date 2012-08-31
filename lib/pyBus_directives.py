#!/usr/bin/python

import os, sys, time, signal, json
import pyBus_core as core

#####################################
# GLOBALS
#####################################
# directives list - maps function to src:dest:data
# first level of directives is filtering the src, so put in the integer representation of the src
# second level is destination
# third level is data : function name
DIRECTIVES = {
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
      '380400' : 'd_cdScanForward',
      '380401' : 'd_cdScanBackard',
      '380800' : 'd_cdRandom',
      '380801' : 'd_cdRandom'
    }
  }
}

WRITER = None

#####################################
# FUNCTIONS
#####################################
# INIT
def init(writer):
  global WRITER
  WRITER = writer

# MANAGE PACKET!
def manage(packet):
  src = packet['src']
  dst = packet['dst']
  dataString = ''.join(packet['dat'])
  methodName = None

  try:
    if (src not in DIRECTIVES.keys()):
      return False
    srcDir = DIRECTIVES[src]
    if (dst not in srcDir.keys()):
      return False
    dstDir = srcDir[dst]
    if (dataString not in dstDir.keys()) and ('ALL' not in dstDir.keys()):
      return False
    if ('ALL'  in dstDir.keys()):
      methodName = dstDir['ALL']
    else:
      methodName = dstDir[dataString]
    
  except Exception, e:
    core.printOut(e, 2)
    
  if methodName:
    methodToCall = globals()[methodName]
    core.printOut("Directive found for packet:", 0)
    core.displayPacket(packet, 0)
    result = methodToCall(packet)
    return result

  else:
    core.printOut("Directive not found for packet:", 1)
    core.displayPacket(packet, 1)
    return None

  globalManage(packet)
  
#####################################
# All directives should have a d_ prefix as we are searching GLOABBLY for function names.. so best have unique enough names
def globalManage(packet):
  if not REGISTERED:
    WRITER.writeBusPacket('18', 'FF', ['02', '01'])

def d_custom_IKE(packet):
  packet_data = packet['dat']
  if packet_data[0] == '18':
    speed = int(packet_data[1], 16) * 2
    revs = int(packet_data[2], 16)
    customState = {'speed' : speed, 'revs' : revs}
    core.writeCustomData(customState)
    speedTrigger(speed)


def d_cdNext(packet):
  core.pB_audio.next()
  trackID = '%02X' % int(core.pB_audio.getTrackID())
  WRITER.writeBusPacket('18', '68', ['39', '02', '09', '00', '3F', '00', '01', '01'])
  core.pB_display.setMode('cd_track', 'cd_progress')

def d_cdPrev(packet):
  core.pB_audio.previous()
  trackID = '%02X' % int(core.pB_audio.getTrackID())
  WRITER.writeBusPacket('18', '68', ['39', '02', '09', '00', '3F', '00', '01', '01'])
  core.pB_display.setMode('cd_track', 'cd_progress')
  
def d_cdScanForward(packet):
  WRITER.writeBusPacket('18', '68', ['39', '03', '09', '00', '3F', '00', '01', '01'])
  core.pB_audio.seek(2)

def d_cdScanBackard(packet):
  WRITER.writeBusPacket('18', '68', ['39', '04', '09', '00', '3F', '00', '01', '01'])
  core.pB_audio.seek(-2)

def d_cdStopPlaying(packet):
  core.pB_audio.pause()
  WRITER.writeBusPacket('18', '68', ['39', '00', '02', '00', '3F', '00', '01', '00'])
  core.pB_display.setMode('') # Clears out the mode to prevent strings being sent
  core.pB_display.instantText('') # Sets the current string empty for next write

def d_cdStartPlaying(packet):
  core.pB_audio.play()
  trackID = '%02X' % int(core.pB_audio.getTrackID())
  WRITER.writeBusPacket('18', '68', ['39', '00', '09', '00', '3F', '00', '01', '01'])
  core.pB_display.setMode('cd_track', 'cd_progress')
 
def d_cdSendStatus(packet):
  trackID = '%02X' % int(core.pB_audio.getTrackID())
  WRITER.writeBusPacket('18', '68', ['39', '00', '09', '00', '3F', '00', '01', '01'])

def d_cdPollResponse(packet):
  core.REGISTERED = True
  WRITER.writeBusPacket('18', 'FF', ['02','00'])
  
def d_cdRandom(packet):
  packet_data = packet['dat']
  if packet_data[2] == '00':
    core.pB_audio.random(0)
    core.pB_display.instantText('Random OFF')
  if packet_data[2] == '01':
    core.pB_audio.random(1)
    core.pB_display.instantText('Random ON')
   
def speedTrigger(speed):
  if (speed > 100):
    fastSong = "Dethklok/Dethklok - The Gears.mp3"
    try:
      if (core.pB_audio.getInfoByPath(fastSong)['id'] != core.pB_audio.getTrackID()):
        core.pB_audio.addSong(fastSong)
        core.pB_audio.playSong(fastSong)
        core.pB_display.setMode('HOLY SHIT', 'cd_progress')
    except:
      print "Exception changing track"
