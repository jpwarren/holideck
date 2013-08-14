#!/usr/bin/env python
"""
Demonstrate the chase function from holiday.py

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

class Chaser(object):
    """
    Implements a chaser
    """
    
    def __init__(self, addr,
                 pattern=None,
                 reverse=False,
                 delay=0.1):
        """
        Controls a single Holiday at addr

        @param pattern: The starting pattern to chase around
        """
        self.hol = holiday.Holiday(addr=addr,
                                   remote=True)

        if pattern is None:
            pattern = [
                (0x00, 0x00, 0x00),
                ] * self.hol.NUM_GLOBES
            pattern[0] = (0xff, 0xff, 0xff)
            pattern[10] = (0xff, 0x00, 0x00)
            pattern[20] = (0x00, 0xff, 0x00)
            pattern[30] = (0x00, 0x00, 0xff)
            pattern[40] = (0xff, 0xff, 0x00)
            
        # Make a copy so we don't clobber the original
        self.globe_pattern = pattern[:]

        self.reverse = reverse
        self.delay = delay

    def animate(self):
        # Animation sequence is to start blank, then light each
        # globe in sequence until all are lit, then start again.
        while True:

            # Move lights one step forwards or backwards,
            # depending on the setting passed in
            if self.reverse:
                new_pattern = self.globe_pattern[1:]
                new_pattern.append(self.globe_pattern[0])
                pass

            else:
                new_pattern = self.globe_pattern[:-1]
                new_pattern.insert(0, self.globe_pattern[-1])
                pass

            self.globe_pattern = new_pattern
            self.hol.set_pattern(self.globe_pattern)
            self.hol.render()
            time.sleep(self.delay)
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

    obj = Chaser(hostname,
                 reverse=False)
    obj.animate()
