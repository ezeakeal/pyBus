import web, os, sys, subprocess, commands, mimetypes, re
import simplejson as JSON
import pyBus_module_audio as pB_audio

def enum(**enums):
  return type('Enum', (), enums)

currentTrackID = -1

urls = (
  '/', 'index',
  '/update', 'update',
  '/getLibrary', 'getLibrary',
  '/getPlaylist', 'getPlaylist',
  '/getInfoPath', 'getInfoPath',
  '/playlistMod', 'playlistMod',
  '/musicStatus', 'musicStatus'
)

render = web.template.render('templates/')
PYBUS_SOCKET_FILE = "/tmp/ibus_custom.log"

#########################
# Internal Functions
######################### 
def getCustomData():
  status = None
  if (os.path.isfile(PYBUS_SOCKET_FILE)):  
    log_file = open(PYBUS_SOCKET_FILE,"r")
    log_file_data = log_file.read()
    log_file.close() 
    try:
      status = JSON.loads(log_file_data)
    except Exception, e:
      print "Error loading custom data file"
      print e
  return(status)

#########################
# Web stuff
#########################  
class index:
  def GET(self):
    pB_audio.init()
    return render.index()

class musicStatus:
  def GET(self):
    global currentTrackID
    status = pB_audio.getInfo(currentTrackID)
    status['custom'] = getCustomData()
    if ('songid' in status['status'].keys()):
      currentTrackID = status['status']['songid']
    return JSON.dumps(status)

class getLibrary:
  def GET(self):
    library = pB_audio.getLibrary()
    return JSON.dumps(library)

class getPlaylist:
  def GET(self):
    playlist = pB_audio.getPlaylist()
    return JSON.dumps(playlist)

class getInfoPath:
  def GET(self):
    getData = web.input(_method='get')
    path = getData.path
    return JSON.dumps(playlist)
    
class playlistMod:
  def GET(self):
    getData = web.input(_method='get')
    if (getData.type == "add"):
      filePath = getData.path
      pB_audio.addSong(filePath)
      
    if (getData.type == "play"):
      filePath = getData.path
      pB_audio.playSong(filePath)

    if (getData.type == "remove"):
      filePath = getData.path
      pB_audio.removeSong(filePath)

    if (getData.type == "pause"):
      status = pB_audio.getInfo(currentTrackID)
      if status['status']['state'] == "stop":
        pB_audio.play()  
      else:
        pB_audio.pause()
    if (getData.type == "next"):
      pB_audio.next()
    if (getData.type == "previous"):
      pB_audio.previous()
    

def init():
  pB_audio.init()
  app = web.application(urls, globals())
  app.run()
