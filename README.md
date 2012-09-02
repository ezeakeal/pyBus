pyBus
=====

iBus interface for my E46 BMW written in Python
This is to be used with the USB interface which can be acquired from [Reslers.de](http://www.reslers.de/IBUS/)

The software expects MPD to be working on whatever it is installed on (for me, hopefully a raspberry Pi - will write something in a blog soon)

## Overview
There are 2 main components:  
**pyBus.py** - interfaces with the iBus to emulate a CD-Changer  
**pyBus_web.py** - Web-Server which will broadcast an interface that allows a user to:  
* Play/Pause
* Next/Previous
* Modify Playlist
* View RPM, current speed

### Useful links
http://linux.die.net/man/5/mpd.conf
http://miro.oorganica.com/raspberry-pi-mpd/

### Warning
All software is in early alpha stages!

### Architecture/Operation
Soooon..

## Pre-Requisites
* python, mpd, python-setuptools
	* apt-get install python python-setuptools mpd 
* *Python modules:* termcolor, web.py, python-mpd, pyserial
	* easy_install termcolor web.py python-mpd pyserial
## How to use
* Install the prerequisites above
* Ensure music is available at /music and that mpd is configured to read from there (best test mpc using mpc prior)
* Plug in iBus USB device
* Run: `./pyBus.py <PATH to USB Device>`
	* E.g. `./pyBus.py /dev/ttyUSB0`

