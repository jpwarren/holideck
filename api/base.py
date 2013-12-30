#!/usr/bin/env python
"""
Base API classes for Holiday interfaces

Copyright (c) 2013 Justin Warren <justin@eigenmagic.com>
License: MIT (see LICENSE for details)
"""

__author__ = "Justin Warren"
__version__ = '0.02-dev'
__license__ = "MIT"

import os
import logging

NUM_GLOBES = holiday.Holiday.NUM_GLOBES

# Set up logging
log = logging.getLogger('base')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s: %(name)s [%(levelname)s]: %(message)s"))
log.addHandler(handler)
log.setLevel(logging.DEBUG)

class HolidayBase(object):
    """
    The base Holiday class for the main API
    """
    NUM_GLOBES = 50

    # Local representation of globe state
    globes = [ (0,0,0), ] * NUM_GLOBES

    def setglobe(self, globenum, r, g, b):
        # FIXME: This should be (self, globenum, color) where color is
        # a tuple of (r g, b).
        """Set a globe"""
        if (globenum < 0) or (globenum >= self.NUM_GLOBES):
            return
        self.globes[globenum] = (r, g, b)

    def fill(self, r, g, b):
        """Sets the whole string to a particular colour"""
        self.globes = [ (int(r), int(g), int(b)), ] * self.NUM_GLOBES
            #for e in self.globes:
            #	e[0] = int(r)
            #	e[1] = int(g)
            #	e[2] = int(b)

    def getglobe(self, globenum):
        """Return a tuple representing a globe's RGB color value"""
        if (globenum < 0) or (globenum >= self.NUM_GLOBES):
            # Fail hard, don't ignore errors
            raise IndexError("globenum %d does not exist", globenum)
        return self.globes[globenum]

    def set_pattern(self, pattern):
        """
        Set the entire string in one go
        """
        if len(pattern) != self.NUM_GLOBES:
            raise ValueError("pattern length incorrect: %d != %d" % ( len(pattern), self.NUM_GLOBES) )
        self.globes = pattern[:]

    def chase(self, direction="True"):
        """Rotate all of the globes around - up if TRUE, down if FALSE"""
        return

    def rotate(self, newr, newg, newb, direction="True", ):
        """Rotate all of the globes up if TRUE, down if FALSE
        Set the new start of the string to the color values"""
        return

    def render(self):
        raise NotImplementedError

class ButtonHoliday(HolidayBase):
    """
    Used when running on a physical Holiday.
    """
    def __init__(self):
        super(ButtonHoliday, self).__init__()
        self.pid = os.getpid()
        self.pipename = '/run/compose.fifo'
        try:
            self.pipe = open(self.pipename, "wb")
        except:
            print "Couldn't open the pipe! Oh no!"
            self.pipe = None
            pass
        
    def render(self):
        """
        Render globe colours to local pipe
        """
        rend = []
        rend.append("0x000010")
        rend.append("0x%06x" % self.pid)
        for g in self.globes:
            tripval = (g[0] << 16) + (g[1] << 8) + g[2]
            rend.append("0x%06x" % tripval)
            pass
        self.pipe.write('\n'.join(rend))
        self.pipe.flush()

class ButtonApp(object):
    """
    A ButtonApp runs on a physical Holiday using the button interface.
    """

    def start(self):
        """
        Do whatever is required to start up the app
        """
        return

    def stop(self):
        """
        Do whatever is required to stop the app
        """
        return

    def up(self):
        """
        Called when the Up button is pressed
        """
        return
    
    def down(self):
        """
        Called when the Down button is pressed
        """
        return
    
