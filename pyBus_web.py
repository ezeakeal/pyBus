#!/usr/bin/python

import os, sys, time, signal

sys.path.append( './lib/' )

import pyBus_module_web as pB_web
import pyBus_core as core

#####################################
# MAIN
#####################################

# Run web interface
pB_web.init()
sys.exit(0)