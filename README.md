pyBus
=====

iBus interface for my E46 BMW written in Python
This is to be used with the USB interface which 
can be acquired from [Reslers.de](http://www.reslers.de/IBUS/)

The software acts as a media center in a BMW. It will use
MPD as it's media manager, and provide an interface between 
that and the radio/steering wheel controls.

## Overview
**pyBus.py** - interfaces with the iBus to emulate a CD-Changer  
**pyBus_web.py** - Web-Server which will broadcast an interface that allows a user to:  
* Play/Pause
* Next/Previous
* Modify Playlist
* View RPM, current speed

### Useful links
http://linux.die.net/man/5/mpd.conf   
http://miro.oorganica.com/raspberry-pi-mpd/   
http://web.comhem.se/bengt-olof.swing/ibusdevicesandoperations.htm   

### Warning
All software is in early alpha stages!

### Architecture/Operation
Soooon..

## Pre-Requisites
* python, mpd, python-setuptools
	* `apt-get install python python-setuptools mpd`
* **Python modules:** termcolor, web.py, python-mpd, pyserial
	* `easy_install termcolor web.py python-mpd pyserial`
## How to use
* Install the prerequisites above
* Ensure music is available at /music and that mpd is configured to read from there (best test mpc using mpc prior)
* Plug in iBus USB device
* Run: `./pyBus.py <PATH to USB Device>`
	* E.g. `./pyBus.py /dev/ttyUSB0`

