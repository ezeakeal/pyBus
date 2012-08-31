#!/usr/bin/python

import os, sys, time, signal, binascii, termcolor, json
import serial
from time import strftime as date

sys.path.append( './lib/' )

import pyBus_directives as directives
import pyBus_module_audio as pB_audio
import pyBus_module_display as pB_display

#####################################
# GLOBALS
#####################################
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

REGISTERED = False

WRITER = None

#------------------------------------
# CLASS for iBus communications
#------------------------------------
class ibusFace ( ):
  # Initialize the serial connection - then use some commands I saw somewhere once
  def __init__(self, devPath):
    self.SDEV = serial.Serial(devPath,
                       baudrate=9600,
                       bytesize=serial.EIGHTBITS,
                       parity=serial.PARITY_EVEN,
                       stopbits=serial.STOPBITS_ONE
                       )
    self.SDEV.setDTR(True)
    self.SDEV.flushInput()

  # Wait for a significant delay in the bus before parsing stuff (signals separated by pauses)
  def waitClearBus(self):
    oldTime = time.time()
    while True:
      # Wait for large interval
      swallow_char = self.readChar() # will be src packet
      newTime = time.time()
      deltaTime = newTime - oldTime
      oldTime = newTime
      if deltaTime > 0.1:
        break # we have found a significant delay in signals, but have swallowed the first character in doing so.
              # So the next code swallows what should be the rest of the packet

    packetLength = self.readChar() # len packet
    self.readChar() # dst packet
    dataLen = int(packetLength, 16) - 2
    while dataLen > 0:
      self.readChar()
      dataLen = dataLen - 1
    self.readChar() # XOR packet

  # Read a packet from the bus
  def readBusPacket(self):
    packet = {
      "src" : None,
      "len" : None,
      "dst" : None,
      "dat" : [],
      "xor" : None
    }
    packet["src"] = self.readChar()
    packet["len"] = self.readChar()
    packet["dst"] = self.readChar()

    dataLen = int(packet['len'], 16) - 2
    dataTmp = []
    while dataLen > 0:
      dataTmp.append(self.readChar())
      dataLen = dataLen - 1
    packet['dat'] = dataTmp
    packet['xor'] = self.readChar()
    return packet

  # Read in one character from the bus and convert to hex
  def readChar(self):
    char = self.SDEV.read(1)
    char = '%02X' % ord(char)
    return char

  def writeChar(self, char):
    wChar = chr(char)
    self.SDEV.write(wChar)
    self.SDEV.flush()

  # get checksum of packet
  def getCheckSum(self, packet):
    chk = 0
    packet.append(0)
    for p in packet:
      chk ^= p
    return chk

  # Write Packet to iBus
  def writeBusPacket(self, src, dst, data):
    length = '%02X' % (2 + len(data))
    packet = [src, length, dst]
    for p in data:
      packet.append(p)

    for i in range(len(packet)):
      packet[i] = int('0x%s' % packet[i], 16)

    chk = self.getCheckSum(packet) 
    lastInd=len(packet) - 1
    packet[lastInd] = chk # packet is an array of int
    
    packetSent = False
    while not packetSent:
      if (self.SDEV.getCTS()):
        packetSent = True
        for p in packet:
          self.writeChar(p)
      else:
        time.sleep(0.02)
        printOut("Waiting for bus to clear before writing!", 3)

  def close(self):
    self.SDEV.close()
#---------- END CLASS -------------

#####################################
# FUNCTIONS
#####################################
def writeCustomData(data):
  logFile = open(IBUS_LOG_FILE, 'w')
  logFile.write(json.dumps(data))
  logFile.close()

# Print the locations in english
def mapBusLocation(hexChar):
  if hexChar not in LOCATIONS.keys():
    return "UNKOWN"
  return LOCATIONS[hexChar]

# print coloured 
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

  
# Print out the packet received in a nice way
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
  
# Never ending loop to read the packets on the bus and run commands on them in some cases
def readBusLoop():
  print "In read loop"
  while True:
    packet = WRITER.readBusPacket()
    directives.manage(packet)

def initSignals():
  print "Sending initialize signals"
  WRITER.writeBusPacket('18', 'FF', ['02', '01'])

def initialize(devPath):
  global WRITER, LOG_ERROR, LOG_STDRD
  LOG_ERROR = open(LOGFILE_ERROR, 'a')
  LOG_STDRD = open(LOGFILE_STDRD, 'a')
  WRITER = ibusFace(devPath)
  pB_audio.init()
  pB_display.init(WRITER)
  directives.init(WRITER)

  # Wait for the iBus to clear 
  print "Waiting for clear bus"
  WRITER.waitClearBus()
  print "Bus clear!"
  initSignals()

def closeBus():
  pB_display.end()
  WRITER.close()
  LOG_ERROR.close()
  LOG_STDRD.close()
  pB_audio.stop()

def run():
  readBusLoop()