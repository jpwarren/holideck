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
import math
import colorsys

from api.base import HolidayBase
#from api.restholiday import RESTHoliday
from api.udpholiday import UDPHoliday

NUM_GLOBES = HolidayBase.NUM_GLOBES

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

        self.add_option('-a', '--anim-sleep', dest='anim_sleep',
                        help="Sleep time between animation frames",
                        type="float", default=0.1)

        self.add_option('-c', '--color', dest='colorset',
                         help="Color of the string(s)",
                         action='append', default=[])

        self.add_option('', '--reverse', dest='forwards',
                        help="Reverse direction of animation", 
                        action="store_false", default=True)
        
        self.add_option('', '--switchback', dest='switchback',
                        help="'Switchback' strings, make a single string display like it's "
                        "more than one every m globes",
                        type="int")

        self.add_option('', '--sb-gap', dest='sb_gap',
                        help="Have a gap of n globes between each switchback",
                        type="int", default=0)
        
        self.add_option('', '--disable-swapdir', dest='disable_swapdir',
                        help="Disables swapping direction with each switchback", 
                        action="store_true", default=False)
        
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

        if self.options.colorset:
            import webcolors
            colorset = [ webcolors.hex_to_rgb(x) for x in self.options.colorset ]
            self.options.colorset = colorset

class vHoliday(object):
    """
    A 'virtual' Holiday, used for implementing switchback mode and
    other things on n real Holidays.

    A virtual Holiday can be shorter than a real Holiday, or exactly
    as long; it cannot (for now) be longer than a real one.

    FIXME: Enable a virtual Holiday to be longer than a real Holiday
    so we could span Holidays if we wanted to.
    """
    def __init__(self, hols=None, start=0, length=NUM_GLOBES, direction=True):
        """
        Each parameter is a list of one or more physical Holidays

        @param hols: a list of Holiday objects to talk to
        @param start: The starting offset for this virtual holiday
        @param length: the length of this virtual Holiday
        @param direction: If True, move from low to high idx, if False, from high to low idx
        """
        if hols is None:
            self.hols = []
            self.hols.append(UDPHoliday('localhost', 9988))
        else:
            self.hols = hols
            pass

        self.start = start
        if length > NUM_GLOBES:
            raise ValueError("Virtual Holidays cannot be longer than real ones.")
        self.length = length

        self.direction = direction

    def map_globe_idx(self, srcidx):
        """
        Map the 'virtual' globe index onto the 'real' holiday and globe index
        """
        # positive direction
        if self.direction:
            dstidx = self.start + srcidx
        else:
            dstidx = self.start + self.length - srcidx - 1
            pass

        # Check we haven't gone off the end of our 'virtual' string
        if abs(dstidx - self.start) > self.length:
            raise ValueError("globe %d not valid on this vHoliday" % srcidx)

        holid = 0
        return (holid, dstidx)

    # Implement the standard Holiday API for the virtual Holiday
    def getglobe(self, globenum):
        holid, idx = self.map_globe_idx(globenum)
        return self.hols[holid].getglobe(idx)

    def setglobe(self, globenum, color):
        holid, idx = self.map_globe_idx(globenum)
        #log.debug("set globe: %d %s [ %d, %d ]", globenum, color, holid, idx)
        res = self.hols[holid].setglobe(idx, color[0], color[1], color[2])

    def set_pattern(self, pattern):
        for globenum, color in enumerate(pattern):
            holid, idx = self.map_globe_idx(globenum)
            self.hols[holid].setglobe(idx, color[0], color[1], color[2])
            pass
        pass

    def fill(self, color):
        for hol in self.hols:
            hol.fill(color[0], color[1], color[2])
            pass
        pass

    def chase(self, direction=True):
        raise NotImplementedError

    def rotate(self, direction=True):
        raise NotImplementedError

    def render(self):
        """
        Render all physical Holidays mapped to this virtual Holiday
        """
        for hol in self.hols:
            hol.render()
    
class PhlostonString(vHoliday):
    """
    A PhlostonString is a Holiday turned into a Phloston Paradise visual alarm light.

    Turns a Holiday into Phloston Paradise hotel evacuation lighting, from the movie
    The Fifth Element.
    """
    def __init__(self, hols=None, start=0,
                 length=NUM_GLOBES, direction=True,
                 color=None, pattern=None):    
        """
        @param color: An (r,g,b) tuple of the lights colour
        @param pattern: An optional pattern of light colours to use
        """
        super(PhlostonString, self).__init__(hols, start, length, direction)

        if pattern is not None:
            self.pattern = pattern
        elif color is not None:
            self.pattern = [ color, ] * length
        else:
            self.pattern = [ (0xaa, 0x00, 0x00), ] * length
            pass

        self.numlit = 0

    def animate(self, forwards=True):
        # Animation sequence is to start blank, then light each
        # globe in sequence until all are lit, then start again.

        # Run animation 'forwards'
        if forwards:
            # Light the globes that are lit
            for i in range(0, self.numlit):
                #log.debug("lit: %d", i)
                self.setglobe(i, self.pattern[i])
                pass

            # Blank those that are not lit
            for i in range(self.numlit, self.length+1):
                #log.debug("unlit: %d", i)
                self.setglobe(i, (0x00, 0x00, 0x00))
                pass
        else:
            # Light the globes that are lit
            for i in range(0, self.numlit):
                #log.debug("lit: %d", i)
                self.setglobe(self.length-i-1, self.pattern[i])
                pass

            # Blank those that are not lit
            for i in range(self.numlit, self.length+1):
                #log.debug("unlit: %d", i)
                self.setglobe(self.length-i-1, (0x00, 0x00, 0x00))
                pass
            
        self.numlit += 1
        if self.numlit > self.length:
            self.numlit = 0
            pass

    def set_pattern(self, pattern):
        if len(pattern) > self.length:
            self.pattern = pattern[:self.length]
        elif len(pattern) < self.length:
            # blank pad out short patterns
            self.pattern = pattern + ( [(0,0,0),] * (self.length - len(self.pattern)) )
        else:
            self.pattern = pattern
        
if __name__ == '__main__':

    usage = "Usage: %prog [options] [<addr:port>]"
    optparse = PhlostonOptions()

    options, args = optparse.parseOptions()

    hols = []
    if len(args) > 1:
        for arg in args:
            hol_addr, hol_port = arg.split(':')
            hols.append(UDPHoliday(ipaddr=hol_addr, port=int(hol_port)))
    else:
        hol_addr, hol_port = args[0].split(':')
        for i in range(options.numstrings):
            hols.append(UDPHoliday(ipaddr=hol_addr, port=int(hol_port)+i))
            pass

    # Figure out how many 'virtual' strings we have
    vhols = []

    if options.switchback:
        length = options.switchback
        pieces = int(math.floor(float(NUM_GLOBES) / options.switchback))

    else:
        length = NUM_GLOBES
        pieces = 1
        pass
        
    num_vhols = pieces * options.numstrings

    if options.colorset:
        # Use the last defined color to make up the full set
        # This allows us to define one color for all strings,
        # or up to n of m total string colors
        if len(options.colorset) < num_vhols:
            lastcolor = options.colorset[-1]
            for i in range( num_vhols - len(options.colorset) ):
                options.colorset.append(lastcolor)
                pass
            pass
    
    for i in range(num_vhols):
        # Use the same physical holiday for each chunk of pieces
        holid = int(i / pieces)
        if options.disable_swapdir:
            direction = True
        else:
            direction = not (i % 2)

        start = length * (i % pieces)
        if i > 0:
            start += options.sb_gap
            pass
        
        #log.debug("holid: %d, direction: %d, start: %d", holid, direction, start)
        if options.colorset:
            vhol = PhlostonString( [hols[holid], ],
                                   start,
                                   length,
                                   direction,
                                   options.colorset[i])
        else:
            vhol = PhlostonString( [hols[holid], ],
                                   start,
                                   length,
                                   direction)
        vhols.append(vhol)
        pass

    while True:
        for i, hol in enumerate(vhols):
            vhols[i].animate(options.forwards)
            pass

        for hol in hols:
            hol.render()
        
        # Wait for next timetick
        time.sleep(options.anim_sleep)
        pass
    pass

