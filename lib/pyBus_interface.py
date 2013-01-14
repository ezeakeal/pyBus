import serial, time, logging

#------------------------------------
# CLASS for iBus communications
#------------------------------------
class ibusFace ( ):
  # LOCATIONS, a mapping of hex codes seen in SRC/DST parts of packets. This WILL change across models/years.
  LOCATIONS = {
    '00' : 'Broadcast',
    '18' : 'CDW - CDC CD-Player',
    '30' : '?????',
    '3B' : 'NAV Navigation/Videomodule',
    '43' : 'MenuScreen',
    '44' : 'Ignition?',
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

  # Initialize the serial connection - then use some commands I saw somewhere once
  def __init__(self, devPath,):
    self.SDEV = serial.Serial(
      devPath,
      baudrate=9600,
      bytesize=serial.EIGHTBITS,
      parity=serial.PARITY_EVEN,
      stopbits=serial.STOPBITS_ONE
    )
    self.SDEV.setDTR(True)
    self.SDEV.flushInput()
    self.SDEV.lastWrite = int(round(time.time() * 1000))
    logging.debug("Initialized iBus")

  # Wait for a significant delay in the bus before parsing stuff (signals separated by pauses)
  def waitClearBus(self):
    logging.debug("Waiting for clear bus")
    oldTime = time.time()
    while True:
      # Wait for large interval between packets
      swallow_char = self.readChar() # will be src packet if there was a significant delay between packets. Otherwise its nothing useful
      newTime = time.time()
      deltaTime = newTime - oldTime
      oldTime = newTime
      if deltaTime > 0.1:
        break # we have found a significant delay in signals, but have swallowed the first character in doing so.
              # So the next code swallows what should be the rest of the packet

    packetLength = self.readChar() # len packet
    self.readChar() # dst packet
    dataLen = int(packetLength, 16) - 2 # Determind length of this packet from the packetLength variable, then swallow that
    while dataLen > 0:
      self.readChar()
      dataLen = dataLen - 1
    self.readChar() # XOR packet. This will be the last bit of the packet. I could change the while loop variable by one, but this adds clarity.

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
    if dataLen > 20:
      logging.critical("Length of +20 found, no useful packet is this long.. cleaning up")
      self.waitClearBus()
      return None

    dataTmp = []
    while dataLen > 0:
      dataTmp.append(self.readChar())
      dataLen = dataLen - 1
    packet['dat'] = dataTmp
    packet['xor'] = self.readChar()
    valStr = [packet['src'], packet['src'], packet['len'], packet['dst'], packet['dat'], packet['xor']]
    logging.debug("READ: %s" % valStr)
    return packet

  # Read in one character from the bus and convert to hex
  def readChar(self):
    char = self.SDEV.read(1)
    try:
      char = '%02X' % ord(char)
    except SerialException, e: 
      logging.warning("Hit a serialException: %s" % e)
      pass
    return char

  # Write a string of data created from complete contents of packet
  def writeFullPacket(self, packet):
    data = ''.join(chr(p) for p in packet)
    self.SDEV.write(data)
    self.SDEV.flush()

  # get the checksum of a complete packet to be appended to the packet - I think everything listening on ibus checks these packets (except for this tool)
  def getCheckSum(self, packet):
    chk = 0
    packet.append(0)
    for p in packet:
      chk ^= p
    return chk

  # Write Packet to iBus, first length is determined, the packet is then constructed and a checksum generated/appended.
  # The packet is then sent if the CTS signal is good (Clear To Send)
  # TODO: Read to verify the packet we send is seen
  def writeBusPacket(self, src, dst, data):
    time.sleep(0.01) # pause a tick
    length = '%02X' % (2 + len(data))
    packet = [src, length, dst]
    for p in data:
      packet.append(p)

    logging.debug("WRITE: %s" % packet)
    for i in range(len(packet)):
      packet[i] = int('0x%s' % packet[i], 16)

    chk = self.getCheckSum(packet) 
    lastInd=len(packet) - 1
    packet[lastInd] = chk # packet is an array of int
    
    packetSent = False
    while not packetSent:
      if (self.SDEV.getCTS()) and ((int(round(time.time() * 1000)) - self.SDEV.lastWrite) > 10): # dont write packets to close together.. issues arise
        packetSent = True
        self.writeFullPacket(packet)
        logging.debug("WRITE: SUCCESS")
        self.SDEV.lastWrite = int(round(time.time() * 1000))
      else:
        logging.debug("WRITE: WAIT")
        time.sleep(0.01)
        logging.info("Waiting for bus to clear before writing!")

  def close(self):
    self.SDEV.close()
#---------- END CLASS -------------
