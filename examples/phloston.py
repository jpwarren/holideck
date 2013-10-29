#!/usr/bin/env python
"""
Phloston Paradise Bomb-in-the-hotel style display for MooresCloud Holiday

Copyright (c) 2013 Justin Warren <justin@eigenmagic.com>
License: MIT (see LICENSE for details)
"""

__author__ = "Justin Warren"
__version__ = '0.02-dev'
__license__ = "MIT"

import sys
import time
import logging
import optparse

import holiday
from secretapi.holidaysecretapi import HolidaySecretAPI

# Simulator default address
SIM_ADDR = "localhost:8080"

log = logging.getLogger(sys.argv[0])
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s: %(name)s [%(levelname)s]: %(message)s"))
log.addHandler(handler)
log.setLevel(logging.DEBUG)

class PhlostonOptions(optparse.OptionParser):
    """
    Command-line options parser
    """
    def __init__(self, *args, **kwargs):
        optparse.OptionParser.__init__(self, **kwargs)
        self.addOptions()

    def addOptions(self):
        self.add_option('-n', '--numstrings', dest='numstrings',
                        help="Number of Holiday strings to use [%default]",
                        type="int", default=1)

        # Comms mode, TCP or UDP
        self.add_option('-m', '--mode', dest='mode',
                        help="Communications mode, UDP or TCP [%default]",
                        type="choice", choices=['udp', 'tcp'], default='tcp')

        # Port to start at if we use multiple Holidays
        self.add_option('-p', '--portstart', dest='portstart',
                        help="Port number to start at for strings [%default]",
                        type="int", default=8080)

        self.add_option('-f', '--fps', dest='fps',
                        help="Frames per second, used to slow down data sending",
                        type="int", default=30)

        
    def parseOptions(self):
        """
        Emulate twistedmatrix options parser API
        """
        options, args = self.parse_args()
        self.options = options
        self.args = args

        self.postOptions()

        return self.options, self.args

    def postOptions(self):
        if len(self.args) < 1:
            self.args = [ SIM_ADDR, ]
            pass

        # If we want more strings than we have arguments,
        # then use the first argument as the base addr:port combo
        # for the set, and increment port numbers. This behaviour
        # is used with the simulator. If we specify all of them
        # individually, then the arguments length is how many
        # strings we have, and overrides the -n setting
        if self.options.numstrings < len(self.args):
            self.options.numstrings = len(self.args)
        pass

class PhlostonString(object):
    """
    A PhlostonString is a Holiday turned into a Phloston Paradise visual alarm light.

    Turns a Holiday into Phloston Paradise hotel evacuation lighting, from the movie
    The Fifth Element.
    """
    
    def __init__(self, addr,
                 color=(0xff, 0xff, 0xff),
                 mode='tcp',
                 delay=0.02):
        """
        Controls a single Holiday at addr

        @param addr: Address of the remote Holiday IoTAS controller
        @param color: The color of the lights
        @param delay: Time between lighting each globe
        """
        if mode == 'tcp':
            self.hol = holiday.Holiday(addr=addr,
                                       remote=True)
        elif mode == 'udp':
            addr, port = addr.split(':')
            self.hol = HolidaySecretAPI(addr, int(port))
            
        self.color = color

        self.numlit = 0

        self.base_pattern = [
            (0x00, 0x00, 0x00),
            ] * self.hol.NUM_GLOBES

        # Make a copy so we don't clobber the original
        self.globe_pattern = self.base_pattern[:]

    def animate(self):
        # Animation sequence is to start blank, then light each
        # globe in sequence until all are lit, then start again.

        self.numlit += 1
        if self.numlit > self.hol.NUM_GLOBES:
            self.numlit = 0
            self.globe_pattern = self.base_pattern[:]
            pass
        else:
            for i in range(self.numlit):
                self.globe_pattern[i] = self.color
                pass
            #log.debug("Pattern is: %s", self.globe_pattern)
            self.hol.set_pattern(self.globe_pattern)
            self.hol.render()
            pass
        pass
        
if __name__ == '__main__':

    usage = "Usage: %prog [options] [<addr:port>]"
    optparse = PhlostonOptions()

    options, args = optparse.parseOptions()

    phlostons = []

    colorset = [
        (0x33, 0x88, 0x33),
        (0x88, 0x33, 0x33),
        (0x00, 0x33, 0x88),
        (0x88, 0x88, 0x33),
        (0x33, 0x88, 0x88),
        ]
    if options.numstrings > len(colorset):
        colorset = colorset * ( int(options.numstrings/len(colorset))+1)
        pass

    for i in range(options.numstrings):
        if options.numstrings > len(args):
            addr, port = args[0].split(':')
            port = int(port) + i
            ps_addr = "%s:%s" % (addr, port)
            pass
        else:
            ps_addr = args[i]
            pass

        ps = PhlostonString(ps_addr,
                            mode=options.mode,
                            color=colorset[i],)
        phlostons.append(ps)

        pass

    # Time limiting bits to slow down the UDP firehose
    # This is stupid, but functional. Should be event driven, probably.
    sleeptime = 1.0/options.fps

    while True:
        for i in range(options.numstrings):
            phlostons[i].animate()
            pass
        # Wait for next timetick
        time.sleep(sleeptime)
        pass
    pass

