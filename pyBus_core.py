#!/usr/bin/python

import os
import json
import time
import logging
import random

# Here we import the two types of drivers. The event driven driver, and the ticking driver.
import lib.pyBus_eventDriver as pB_eDriver  # For responding to signals
from lib.pyBus_interface import *

logger = logging.getLogger(__name__)


#####################################
# FUNCTIONS
#####################################

class DirectiveHandler(object):
    directive_file = "../directives.json"
    speed_switch = False

    def __init__(self, writer, display, audio):
        logger.info("Initializing directive handler")
        self._load_directives()
        self.writer = writer
        self.display = display
        self.audio = audio

    def _load_directives(self):
        directive_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            self.directive_file
        )
        if not os.path.exists(directive_path):
            raise IOError("Can't find the directives file at: %s" % directive_path)
        # Load up and sanitize the keys(hex patterns)
        with open(directive_path, "r") as f:
            directives = json.load(f)
        self.directives = {self._sanitize(hpattern): dest_func_name
                           for hpattern, dest_func_name in directives.items()}
        directive_func_calls = list(set(self.directive_map.values()))
        logger.info("The following functions are mapped to Ibus codes: %s" % directive_func_calls)
        for func_name in directive_func_calls:
            assert getattr(self, func_name) is not None, "Function %s not found!" % func_name

    def _sanitize(self, hstring):
        sanstr = hstring.replace(" ", "")
        sanstr = sanstr.lower()
        return sanstr

    def handle_code(self, hexstr):
        func_name = self.directives.get(hexstr)
        if not func_name:
            logger.info("Pattern [%s] has no directive function" % hexstr)
            return
        dest_func = getattr(self, func_name)
        if not dest_func:
            raise Exception("Function %s is referenced by directives, but can't be found!" % func_name)
        logger.info("Received [%s] - calling %s" % (hexstr, func_name))
        result = dest_func(hexstr)
        return result

    def _display_track_info(self, name=True, position=True):
        """Display track info on display"""
        if name:
            self.display.queue(self._get_track_name(), priority=False)
        if position:
            self.display.queue(self._get_position(), priority=False)

    def __get_mpd_status(self, status_param='song'):
        status = self.audio.getInfo()
        if 'status' in status:
            mpd_status = status['status']
            return getattr(mpd_status, status_param, 0)

    def _get_position(self):
        """Returns the string 'X of Y'
        Where X is current song number, Y is total count"""
        song_idx = int(self.__get_mpd_status()) + 1
        playlist_len = int(self.__get_mpd_status(status_param='playlistlength'))
        return "%s of %s" % (song_idx, playlist_len)

    def _get_track_number(self):
        """Gets the track number in 2 parts; hundreds and 0-99
        Reason is that the display starts interpreting numbers > 99 as ascii, so we split it
        """
        song_idx = int(self.__get_mpd_status()) + 1
        return song_idx / 100, song_idx % 100

    # Get the track text to put in display stack
    def _get_track_name(self):
        display_que = []
        status = self.audio.getInfo()
        if 'track' in status:
            track_status = status['track']
            if track_status:
                if 'artist' in track_status:
                    display_que.append(status['track']['artist'])
                if 'title' in track_status:
                    display_que.append(status['track']['title'])
            else:
                display_que.append("Paused")
        return display_que


class Directives(DirectiveHandler):
    def d_keyOut(self, packet):
        self.writer.writeBusPacket('3F', '00', ['0C', '53', '01'])  # Put up window 1
        self.writer.writeBusPacket('3F', '00', ['0C', '42', '01'])  # Put up window 2
        self.writer.writeBusPacket('3F', '00', ['0C', '55', '01'])  # Put up window 3
        self.writer.writeBusPacket('3F', '00', ['0C', '43', '01'])  # Put up window 4

    def d_toggleSS(self, packet):
        """Toggles a speed switch variable, allowing actions when crossing a speed threshold"""
        self.speed_switch = not self.speed_switch
        self.display.immediateText('SpeedSw: On' if self.speed_switch else 'SpeedSw: Off')

    def d_togglePause(self, packet):
        """Toggles pause"""
        status = self.audio.getInfo()
        if (status['status']['state'] != "play"):
            self.audio.play()
            self.display.immediateText('Play')
        else:
            self.audio.pause()
            self.display.immediateText('Paused')

    def d_update(self, packet):
        """Attempts to update the MPD library"""
        self.display.immediateText('Updating')
        self.audio.update()
        self.audio.addAll()

    def d_shutdown(self, packet):
        """Attempts to shutdown PyBus - Use Supervisord to restart always"""
        self.display.immediateText('Shutdown')
        raise Exception("Restart Triggered")

    # This packet is used to parse all messages from the IKE (instrument control electronics), as it contains speed/RPM info. But the data for speed/rpm will vary, so it must be parsed via a method linked to 'ALL' data in the JSON DIRECTIVES
    def d_all_IKE(self, packet):
        """Parse all IKE data"""
        packet_data = packet['dat']
        if packet_data[0] == '18':
            if not self.speed_switch:
                return
            speed = int(packet_data[1], 16) * 2
            revs = int(packet_data[2], 16)
            self.speed_trigger(speed)

    def speed_trigger(self, speed):
        """Jumps to a particular song, at a particular point in the song"""
        speedsong_choices = {
            # "Song path": seconds
            "The Prodigy/Invaders Must Die.mp3": 49,
            "Edguy/Mandrake/05 - Wake Up The King.mp3": 93,
            "Killswitch Engage - Holy Diver": 144
        }
        if (speed > 100):
            # Pick a random song
            song_names = speedsong_choices.keys()
            song_index = random.randint(0, len(song_names) - 1)
            song_name = song_names[song_index]
            # Play the song
            self.audio.playSong(song_name)
            # Seek into song
            self.audio.seek(speedsong_choices[song_name])
            self.put_windows_down()

    def put_windows_down(self):
        self.writer.writeBusPacket('3F', '00', ['0C', '52', '01'])  # Put down window 1
        self.writer.writeBusPacket('3F', '00', ['0C', '41', '01'])  # Put down window 2
        self.writer.writeBusPacket('3F', '00', ['0C', '54', '01'])  # Put down window 3
        self.writer.writeBusPacket('3F', '00', ['0C', '44', '01'])  # Put down window 4

    def put_windows_up(self):
        self.writer.writeBusPacket('3F', '00', ['0C', '53', '01'])  # Put up window 1
        self.writer.writeBusPacket('3F', '00', ['0C', '42', '01'])  # Put up window 2
        self.writer.writeBusPacket('3F', '00', ['0C', '55', '01'])  # Put up window 3
        self.writer.writeBusPacket('3F', '00', ['0C', '43', '01'])  # Put up window 4

    def d_cdNext(self, packet):
        """Switch to next song"""
        self.audio.next()
        self.write_current_track()
        self.display_track_info()

    def d_cdPrev(self, packet):
        """Switch to previous song"""
        self.audio.previous()
        self.write_current_track()
        self.display_track_info()

    def write_current_track(self):
        """Tells the iBus what track we are on for its own display purposes"""
        cdSongHundreds, cdSong = self._get_track_number()
        self.writer.writeBusPacket('18', '68', ['39', '02', '09', '00', '3F', '00', cdSongHundreds, cdSong])

    def d_cdScanForward(self, packet):
        """Scan forward in track - not reliable

        The following packets are received for start/end scanning
        2013/03/24T06:52:22 [DEBUG in pyBus_interface] READ: ['68', '05', '18', ['38', '04', '01'], '48']
        2013/03/24T06:52:24 [DEBUG in pyBus_interface] READ: ['68', '05', '18', ['38', '03', '00'], '4E']
        """
        cdSongHundreds, cdSong = self._get_track_number()
        if "".join(packet['dat']) == "380401":
            self.writer.writeBusPacket(
                '18', '68', [
                    '39', '03', '09', '00', '3F', '00',
                    cdSongHundreds, cdSong
                ])  # Fast forward scan signal
            self.ticker.enableFunc("scanForward", 0.2)

    def d_cdScanBackward(self, packet):
        """Scan backwards in track - not reliable"""
        cdSongHundreds, cdSong = self._get_track_number()
        self.writer.writeBusPacket(
            '18', '68', [
                '39', '04', '09', '00', '3F', '00',
                cdSongHundreds, cdSong
            ])  # Fast backward scan signal
        if "".join(packet['dat']) == "380400":
            self.ticker.enableFunc("scanBackward", 0.2)

    def d_cdStopPlaying(self, packet):
        """Stop playing, turn off display writing"""
        self.audio.pause()
        self.display.setDisplay(False)
        cdSongHundreds, cdSong = self._get_track_number()
        self.writer.writeBusPacket('18', '68', ['39', '00', '02', '00', '3F', '00', cdSongHundreds, cdSong])

    def d_cdStartPlaying(self, packet):
        """Start playing song, enable display writing"""
        self.audio.pause()
        self.audio.play()
        self.display.setDisplay(True)
        self.ticker.disableAllFunc()
        self._write_current_track()
        self._display_track_info()

    def d_cdSendStatus(self, packet):
        """I didn't understand this back then, and I don't now"""
        self._write_current_track()
        self._display_track_info()

    def d_cdPollResponse(self, packet):
        """Respond to the Poll for changer alive"""
        self.ticker.disableFunc("announce")  # stop announcing
        self.ticker.disableFunc("pollResponse")
        self.ticker.enableFunc("pollResponse", 30)

    def d_cdRandom(self, packet):
        """Toggle Random"""
        random = self.audio.random(0, True)
        self.display.immediateText('Random: ON' if random else 'Random: OFF')
        self._display_track_info(False)

    def d_testSpeed(self, packet):
        """Test the Speed Trigger function"""
        self.speed_trigger(110)

    def d_standup(self, packet):
        """Go to a specific track - I had 90minute standup tracks here"""
        self.display.immediateText('Comedy')
        self.audio.playSong("Standup/first.mp3")


# Initializes modules as required and opens files for writing
def initialize():
    global IBUS, REGISTERED, DEVPATH
    REGISTERED = False

    # Initialize the iBus interface or wait for it to become available.
    while IBUS == None:
        if os.path.exists(DEVPATH):
            IBUS = ibusFace(DEVPATH)
        else:
            logging.warning("USB interface not found at (%s). Waiting 1 seconds.", DEVPATH)
            time.sleep(2)
    IBUS.waitClearBus()  # Wait for the iBus to clear, then send some initialization signals

    pB_eDriver.init(IBUS)


# close the USB device and whatever else is required
def shutdown():
    global IBUS
    logging.info("Shutting down event driver")
    pB_eDriver.shutDown()

    if IBUS:
        logging.info("Killing iBUS instance")
        IBUS.close()
        IBUS = None


def run():
    pB_eDriver.listen()
