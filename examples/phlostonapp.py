#!/usr/bin/env python
"""
Phloston Paradise Bomb-in-the-hotel style display for MooresCloud Holiday
ButtonApp version

Copyright (c) 2013 Justin Warren <justin@eigenmagic.com>
License: MIT (see LICENSE for details)
"""

__author__ = "Justin Warren"
__version__ = '0.02-dev'
__license__ = "MIT"

import time
import logging
import colorsys
import threading

from api.base import ButtonHoliday, ButtonApp

from phloston import PhlostonString

log = logging.getLogger('phloston_app')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s: %(name)s [%(levelname)s]: %(message)s"))
log.addHandler(handler)
log.setLevel(logging.DEBUG)

# Amount of time between frames of animation
SNOOZETIME = 0.05

# Amount of hue to change when Up/Down button is pressed (0.0 - 1.0)
HUESTEP = 0.05

# What color to start as. (r,g,b) tuple
START_COLOR = (100,0,0)

class PhlostonApp(ButtonHoliday, ButtonApp):
    """
    An app for a physical Holiday
    """
    def start(self):
        self.t = PhlostonThread()
        self.t.start()

    def stop(self):
        self.t.terminate = True

    def change_hue(self, hdelta):
        """
        Change the color hue by hdelta, a number between -1.0 and +0.1
        """
        (r,g,b) = self.t.get_color()
        # Shift the colour hue by hdelta
        (h,s,v) = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        h += hdelta
        # Wraparound hue
        if h < 0.0:
            h += 1.0
        elif h > 1.0:
            h -= 1.0
            pass
        
        (r,g,b) = colorsys.hsv_to_rgb(h, s, v)
        # Convert to 0-255 range integers
        newcol = (int(r*255.0), int(g*255.0), int(b*255.0))
        self.t.set_color(newcol)
        
    def up(self):
        """
        Make the colour hue shift upwards
        """
        self.change_hue(HUESTEP)

    def down(self):
        self.change_hue(-HUESTEP)        

class PhlostonThread(threading.Thread):
    """
    Singleton thread that runs the animation
    """
    def run(self):
        self.terminate = False

        # A Phloston string on 1 ButtonHoliday
        self.phloston = PhlostonString([ButtonHoliday(),], color=START_COLOR)

        while True:
            if self.terminate:
                return

            # animate
            self.phloston.animate()
            self.phloston.render()

            # sleep
            time.sleep(SNOOZETIME)
        
        pass

    def set_color(self, newcolor):
        """
        Change the color of the string
        """
        if not hasattr(self, 'phloston'):
            return
        self.phloston.set_pattern( [ newcolor, ] * self.phloston.length )

    def get_color(self):
        if not hasattr(self, 'phloston'):
            return (0,0,0)
        color = self.phloston.pattern[0]
        return color
        
if __name__ == '__main__':
    app = PhlostonApp()
    app.start()
    time.sleep(1)

    app.up()
    time.sleep(0.1)
    app.up()

    time.sleep(0.1)
    app.down()

    time.sleep(0.1)
    app.down()

    time.sleep(0.1)
    app.down()

    time.sleep(0.1)
    app.down()

    time.sleep(0.1)
    app.down()

    time.sleep(0.1)
    app.down()

    time.sleep(0.1)
    app.down()
    
    
    time.sleep(3)

    app.stop()
    
