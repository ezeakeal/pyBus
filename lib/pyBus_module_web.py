import web, os, sys, subprocess, commands, mimetypes, re
import json as JSON
import pyBus_module_audio as pB_audio
import xmlrpclib

def enum(**enums):
  return type('Enum', (), enums)

currentTrackID = -1
supserver = xmlrpclib.Server('http://localhost:9001/RPC2')
# http://supervisord.org/api.html

urls = (
  '/', 'dashboard',
  '/media', 'media',
  '/admin', 'admin',
  '/system', 'system',
  
  '/supervisor/getSupStatus', 'getSupStatus',
  '/supervisor/getProcStatus', 'getProcStatus',
  '/supervisor/stopSupProc', 'stopSupProc',
  '/supervisor/startSupProc', 'startSupProc',
  '/supervisor/tailSupProc', 'tailSupProc',
  '/supervisor/clearProcLog', 'clearProcLog',

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
# Supervisor stuff
#########################  
class getSupStatus:
  def GET(self):
    return JSON.dumps(supserver.supervisor.getState())

class getProcStatus:
  def GET(self):
    return JSON.dumps(supserver.supervisor.getAllProcessInfo())

class stopSupProc:
  def GET(self):
    getData = web.input(_method='get')
    procName = getData.get('proc')
    return JSON.dumps(supserver.supervisor.stopProcessGroup(procName))
  
class startSupProc:
  def GET(self):
    getData = web.input(_method='get')
    procName = getData.get('proc')
    return JSON.dumps(supserver.supervisor.startProcessGroup(procName))

class tailSupProc:
  def GET(self):
    getData = web.input(_method='get')
    procName = getData.get('proc')
    offset = getData.get('offset')
    return JSON.dumps(supserver.supervisor.tailProcessStdoutLog(procName, offset, 10240))
  
class clearProcLog:
  def GET(self):
    getData = web.input(_method='get')
    procName = getData.get('proc')
    return JSON.dumps(supserver.supervisor.clearProcessLogs(procName))

#########################
# Web stuff
#########################  
class dashboard:
  def GET(self):
    return render.dashboard()

class media:
  def GET(self):
    pB_audio.init()
    return render.media()

class admin:
  def GET(self):
    return render.admin()

class system:
  def GET(self):
    pB_audio.init()
    return render.system()

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
