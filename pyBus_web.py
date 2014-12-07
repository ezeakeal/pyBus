#!/usr/bin/python
#################################
# IMPORTS
#################################
import os
import sys
import time
import signal
import logging
import traceback
import tornado.web
import tornado.auth
import tornado.ioloop
import tornado.options

sys.path.append( './lib/' )

from tornado import template
from tornado.escape import url_unescape as unescape

# import pyBus_module_web as pB_web
import pyBus_module_audio as pB_audio
import pyBus_core as core

#################################
# GLOBALS
#################################
LOGLEVEL = logging.DEBUG
MEDIA_CACHE = "/tmp/mediacachetable.html"

def cacheMediaTable():
    mediaData=pB_audio.getLibrary()
    loader = template.Loader("templates")
    t = loader.load("mediaTable.html")
    render_string = t.generate(data=mediaData)
    
    with open(MEDIA_CACHE, 'w') as content_file:
	   content_file.write(render_string)	

#################################
# Page Handlers
#################################
class BaseHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        self.clear()
        self.set_status(400)
        returnError(self, status_code, **kwargs)

def returnError(self, status_code, **kwargs):
    formatted_lines = traceback.format_exc().splitlines()
    errorMsg = formatted_lines[-1]
    self.finish(errorMsg)

class mediaPage(BaseHandler):
    def get(self):
    	with open(MEDIA_CACHE, 'r') as content_file:
    		tableContent = content_file.read()
    	self.render("media.html", mediaTabClass="active", commTabClass="", tableContent=tableContent)

class commandPage(BaseHandler):
    def get(self):
        self.render("game.html", mediaTabClass="", commTabClass="active")


class playlistMod(BaseHandler):
    def get(self, actionType, encFilePath):
        filePath = unescape(encFilePath)
        logging.debug("Action (%s) File(%s)" % (actionType, filePath))
        if (actionType == "play"):
            try:
                logging.debug("Playing: %s" % filePath)
                pB_audio.playSong(filePath)
            except Exception, e:
                logging.error("Exception raised from playListModify")
                logging.error(traceback.format_exc())
                

#################################
# MAIN SERVER SETUP
#################################
# Static routing of resources
static_path = os.path.join(os.path.dirname(__file__), "static")
handlers = [
	(r'/', mediaPage),
    (r'/media', mediaPage),
	(r'/mediaCommand/(\w+)/(.+)', playlistMod),
	(r'/commander', commandPage),
    (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': static_path})
]

# Give that bitch some settings. Bitches love settings
settings = dict(
    debug=True,
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    cookie_secret="OWIOWIOWIOWIOOOOOOOOO",  # Sssh... its a secret
    login_url="/login"
)

# Define the application
application = tornado.web.Application(handlers, **settings)


#################################
# MAIN
#################################
# Start the application if we are not used like a module
def runServer(port):
    global LOG
    logging.basicConfig(
	    level=LOGLEVEL,
	    format='%(asctime)s [%(levelname)s in %(module)s] %(message)s', 
	    datefmt='%Y/%m/%dT%I:%M:%S'
	)

    pB_audio.init()
    cacheMediaTable()
    logging.info("Cached media server list")
    application.listen(port)
    logging.info("PyBus listening on port %s" % port)
    tornado.ioloop.IOLoop.instance().start()


def stopServer():
    tornado.ioloop.IOLoop.instance().stop()


if __name__ == "__main__":
    runServer(80)
