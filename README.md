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


### Warning
All software is in early alpha stages!

### Architecture/Operation
Soooon..

## How to use
* Plug in iBus USB device
* Run: `./pyBus.py <PATH to USB Device>`
	* E.g. `./pyBus.py /dev/ttyUSB0`

