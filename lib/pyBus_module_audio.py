#!/usr/bin/python

import pprint, os, sys, time, signal
from mpd import (MPDClient, CommandError)
from socket import error as SocketError
import pyBus_core as core
#####################################
# GLOBALS
#####################################
HOST     = 'localhost'
PORT     = '6600'
PASSWORD = False
CON_ID   = {'host':HOST, 'port':PORT}
VOLUME   = 50

CLIENT   = None
PLAYLIST = None
LIBRARY  = None
T_STATUS = None
#####################################
# FUNCTIONS
#####################################
def mpdConnect(client, con_id):
  try:
    client.connect(**con_id)
  except SocketError:
    return False
  return True

def init():
  global CLIENT, PLAYLIST, LIBRARY
  ## MPD object instance
  CLIENT = MPDClient()
  if mpdConnect(CLIENT, CON_ID):
    print 'Got connected!'
    print 'Updating!'
    CLIENT.update()
    PLAYLIST = CLIENT.playlistinfo()
    LIBRARY = CLIENT.listallinfo()
    CLIENT.repeat(1) # Repeat all tracks
  else:
    print 'fail to connect MPD server.'

def quit():
  CLIENT.disconnect()

def play():
  CLIENT.play()

def stop():
  CLIENT.stop()

def pause():
  CLIENT.pause()

def next():
  CLIENT.next()

def previous():
  CLIENT.previous()

def random(random):
  CLIENT.random(random)

def seek(delta):
  seekDest = int(float(CLIENT.status()['elapsed']) + delta)
  playListID = int(CLIENT.status()['playlist'])
  CLIENT.seek(playListID, seekDest)

def getTrackInfo():
  global T_STATUS
  if ('songid' not in CLIENT.status()):
    return
  currentTID = getTrackID()
  for song in PLAYLIST:
    trackID = song["id"]
    if trackID == currentTID:
      T_STATUS = song

def getInfo(lastID=-1):
  if CLIENT == None:
    init()
  state = CLIENT.status()
  if (state['state'] != "stop"):
    if ("songid" in state):
      songID = state['songid']
      if (songID != lastID):
        getTrackInfo()
    if (T_STATUS == None):
      getTrackInfo()
  status = {"status": state, "track": T_STATUS}
  return status

def getInfoByPath(filePath):
  for song in PLAYLIST:
   path = song["file"]
   if path == filePath:
     return song

def addSong(filepath):
  global PLAYLIST
  if (getInfoByPath(filepath) == None):
    CLIENT.add(filepath)
    PLAYLIST = CLIENT.playlistinfo()

def removeSong(filepath):
  global PLAYLIST
  song = getInfoByPath(filepath)
  CLIENT.deleteid(song['id'])
  PLAYLIST = CLIENT.playlistinfo()

def playSong(filepath):
  song = getInfoByPath(filepath)
  CLIENT.playid(song['id'])

def getPlaylist():
  return PLAYLIST

def getLibrary():
  return LIBRARY

def  getTrackID():
  if ("songid" not in CLIENT.status()):
    print "ERROR:"
    print CLIENT.status()
  try:
    currentTID = CLIENT.status()['songid']
    return currentTID
  except:
    print "Some sort of error occured.."
    return 0
  
