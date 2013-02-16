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
WRITER = None
STATE_DATA = {}
FUNC_STACK = {}
TICK = 1 # sleep interval in seconds used between iBUS reads
TOCK = True

#####################################
# FUNCTIONS
#####################################
# Set the WRITER object (the iBus interface class) to an instance passed in from the CORE module
def init(writer):
  global WRITER
  logging.info("Initializing the iBus interface for tickDriver")
  WRITER = writer

def shutDown():
  global WRITER
  logging.info("Dereferencing iBus interface")
  WRITER = None

def enableFunc(funcName, interval, count=0):
  global FUNC_STACK

  # Prevent the function getting called at slightly different times and flooding the bus. Make sure its not already qeued. If so, just update the spec.
  kickOff = False
  if funcName not in FUNC_STACK.keys():
    kickOff = True

  if getattr(sys.modules[__name__], funcName):
    FUNC_STACK[funcName] = {
      "INTERVAL": interval,
      "COUNT": count
    }
    if kickOff: do_every(funcName) # Begins loop of function calls, each one occurring as close to the interval as possible.
  else:
    logging.warning("No function found (%s)" % funcName)

def disableFunc(funcName):
  global FUNC_STACK
  if funcName in FUNC_STACK.keys():
    del FUNC_STACK[funcName]

#------------------------------------
# THREAD FOR TICKING AND CHECKING EVENTS
#------------------------------------
def do_every(funcName):
  global FUNC_STACK
  funcSpec = FUNC_STACK.get(funcName)
  worker_func = getattr(sys.modules[__name__], funcName)
  if funcSpec and worker_func:
    interval = funcSpec["INTERVAL"]
    count = funcSpec["COUNT"]
    if count != 1:
      FUNC_STACK[funcName]["COUNT"] = count - 1
      threading.Timer(
        interval,
        do_every, [funcName]
      ).start();
    worker_func();
#------------------------------------

#####################################
# Tick Functions
#####################################
def scanForward():
  pB_audio.seek(5)

def scanBackward():
  pB_audio.seek(-5)  

def pollResponse():
  WRITER.writeBusPacket('18', 'FF', ['02','00'])