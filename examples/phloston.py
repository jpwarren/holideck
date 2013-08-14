#!/usr/bin/env python
"""
Phloston Paradise Bomb-in-the-hotel style display for MooresCloud Holiday

Copyright (c) 2013 Justin Warren <justin@eigenmagic.com>
License: MIT (see LICENSE for details)
"""

__author__ = "Justin Warren"
__version__ = '0.01-dev'
__license__ = "MIT"

import sys
import time
import logging

import holiday

# Simulator default address
SIM_ADDR = "localhost:8080"

log = logging.getLogger(sys.argv[0])
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s: %(name)s [%(levelname)s]: %(message)s"))
log.addHandler(handler)
log.setLevel(logging.DEBUG)

class PhlostonString(object):
    """
    A PhlostonString is a Holiday turned into a Phloston Paradise visual alarm light.

    Turns a Holiday into Phloston Paradise hotel evacuation lighting, from the movie
    The Fifth Element.
    """
    
    def __init__(self, addr,
                 color=(0xff, 0xff, 0xff),
                 delay=0.02):
        """
        Controls a single Holiday at addr

        @param addr: Address of the remote Holiday IoTAS controller
        @param color: The color of the lights
        @param delay: Time between lighting each globe
        """
        self.hol = holiday.Holiday(addr=addr,
                                   remote=True)
        self.color = color
        self.delay = 0.02

        self.base_pattern = [
            (0x00, 0x00, 0x00),
            ] * self.hol.NUM_GLOBES

        # Make a copy so we don't clobber the original
        self.globe_pattern = self.base_pattern[:]

    def animate(self):
        # Animation sequence is to start blank, then light each
        # globe in sequence until all are lit, then start again.
        while True:
            for step in range(0, self.hol.NUM_GLOBES):
                #log.debug("Step %d of animation", step)
                if step == 0:
                    # Reset to beginning
                    self.globe_pattern = self.base_pattern[:]
                else:
                    for i in range(0, step):
                        self.globe_pattern[i] = self.color
                        pass
                    pass
                #log.debug("Pattern is: %s", self.globe_pattern)
                self.hol.set_pattern(self.globe_pattern)
                self.hol.render()
                time.sleep(0.02)
                pass
        
if __name__ == '__main__':
    if len(sys.argv) > 1:
        hostname = sys.argv[1]
        log.debug("hostname: %s", hostname)
    else:
        # Assume we're on the simulator
        log.info("Using simulator: %s", SIM_ADDR)
        hostname = SIM_ADDR
        pass

    ps = PhlostonString(hostname,
                        color=(0x33, 0x88, 0x33),)
    ps.animate()
