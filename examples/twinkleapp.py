#!/usr/bin/env python
"""
ButtonApp version of twinkle.py
Makes a Holiday 'twinkle' with various light patterns/styles

Copyright (c) 2013 Justin Warren <justin@eigenmagic.com>
License: MIT (see LICENSE for details)
"""

import threading
import random
import json
import time
import os.path
import colorsys

import webcolors

from api.base import ButtonHoliday, ButtonApp

from simplexnoise import raw_noise_2d

BASEPATH = os.path.abspath(os.path.dirname(__file__))
PATTERN_DIR = os.path.join(BASEPATH, 'patterns')

def load_patternfile(filename):
    with open(filename) as fp:
        pattern = [ webcolors.hex_to_rgb(x) for x in json.load(fp)['lights'] ]
        return pattern
    pass

MODES = [
    # candela mode
    {'twinkle_algo': 'simplex',
     'simplex_damper': 4.0,
     'init_pattern': [(176, 119, 31),] * ButtonHoliday.NUM_GLOBES,
     'chase': None,
     'snoozetime': 0.04,
     },

    # Xmas twinkle
    {'twinkle_algo': 'simplex',
     'simplex_damper': 4.0,
     'init_pattern': load_patternfile(os.path.join(PATTERN_DIR, 'xmas.json')),
     'chase': None,
     'snoozetime': 0.04,
     },

    # Xmas chase
    {'twinkle_algo': 'chase_only',
     'init_pattern': load_patternfile(os.path.join(PATTERN_DIR, 'xmas2.json')),
     'chase': True,
     'snoozetime': 0.5,
     },

    # Australian Green and Gold twinkle
    {'twinkle_algo': 'simplex',
     'simplex_damper': 4.0,
     'init_pattern': load_patternfile(os.path.join(PATTERN_DIR, 'greenandgold.json')),
     'chase': None,
     'snoozetime': 0.04,
     },
    
    # Australian Green and Gold chaser
    {'twinkle_algo': 'chase_only',
     'init_pattern': load_patternfile(os.path.join(PATTERN_DIR, 'greenandgold.json')),
     'simplex_damper': 4.0,
     'chase': True,
     'snoozetime': 0.1,
     },
    
    # Simple random mode
    {'twinkle_algo': 'random_shift',
     'init_pattern': [ (random.randint(0, 130),
                       random.randint(0, 130),
                       random.randint(0, 130)) for x in range(ButtonHoliday.NUM_GLOBES) ],
     'change_chance': 0.5,
     'huestep_max': 0.1,
     'satstep_max': 0.1,
     'valstep_max': 0.1,
     'chase': None,
     'snoozetime': 0.1,
     },

    # Random mode with limits
    {'twinkle_algo': 'random_limits',
     'init_pattern': [ (random.randint(0, 130),
                       random.randint(0, 130),
                       random.randint(0, 130)) for x in range(ButtonHoliday.NUM_GLOBES) ],
     'change_chance': 0.2,
     'huestep_max': 0.05,
     'satstep_max': 0.05,
     'valstep_max': 0.05,

     'huediff_max': 0.3,
     'satdiff_max': 0.3,
     'valdiff_max': 0.3,
     'chase': None,
     'snoozetime': 0.1,
     },

    ]

class Twinkler(object):

    def __init__(self, hol, options):
        self.hol = hol
        self.options = options
        self.noise_array = [ 0, ] * self.hol.NUM_GLOBES

        # initialise the holiday with the options.pattern
        self.set_pattern(options['init_pattern'])
        pass

    def set_pattern(self, pattern):
        self.hol.set_pattern(pattern)
        pass

    def render(self):
        self.hol.render()

    def twinkle_simplex(self, idx):
        nv = raw_noise_2d(self.noise_array[idx],
                          random.random()) / self.options.get('simplex_damper', 4.0)
        self.noise_array[idx] += nv
        if self.noise_array[idx] > 1.0:
            self.noise_array[idx] = 1.0
            pass
        elif self.noise_array[idx] < -1.0:
            self.noise_array[idx] = -1.0
            pass

        ranger = (self.noise_array[idx] + 1.0) / 2.0

        # Adjust colour. 
        (base_r, base_g, base_b) = self.options['init_pattern'][idx]
        #log.debug("adjusting from orig: %d %d %d", base_r, base_g, base_b)
        r = int(base_r * ranger)
        g = int(base_g * ranger)
        b = int(base_b * ranger)
        self.hol.setglobe(idx, r, g, b)
        pass

    def rand_change_colcomp(self, val, stepmax, baseval=None, diffmax=None):
        """
        Change a colour component value from a baseline using a random perturbation
        """
        if baseval is None:
            baseval = val
            pass
        
        valstep = random.random() * stepmax
        # 50% chance of positive or negative step
        if random.randint(0, 1):
            val += valstep
            if diffmax and abs(baseval - val) > diffmax:
                val = baseval + diffmax
                pass
            if val > 1.0:
                val -= 1.0
        else:
            val -= valstep
            if diffmax and abs(baseval - val) > diffmax:
                val = baseval - diffmax
                pass
            if val < 0.0:
                val += 1.0
            pass
        return val

    def twinkle_random_shift(self, idx):
        """
        Randomly change a bulb from its current value
        """
        # % chance of updating a given globe
        if random.random() < self.options['change_chance']:

            r, g, b = self.hol.getglobe(idx)
            (h, s, v) = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            #log.debug("start h s v: %f %f %f", h, s, v)

            # Adjust color components by a random amount
            h = self.rand_change_colcomp(h, self.options['huestep_max'])
            s = self.rand_change_colcomp(s, self.options['satstep_max'])
            v = self.rand_change_colcomp(v, self.options['valstep_max'])

            (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
            #log.debug("r g b: %f %f %f", r, g, b)
            self.hol.setglobe(idx, int(255*r), int(255*g), int(255*b))
            pass
        pass

    def twinkle_random_limits(self, idx):
        """
        Randomly change a bulb from its baseline value within limits
        """
        (base_r, base_g, base_b) = self.options['init_pattern'][idx]
        (base_h, base_s, base_v) = colorsys.rgb_to_hsv(base_r/255.0,
                                                       base_g/255.0,
                                                       base_b/255.0)
        
        # % chance of updating a given globe
        if random.random() < self.options['change_chance']:

            r, g, b = self.hol.getglobe(idx)
            (h, s, v) = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            #log.debug("start h s v: %f %f %f", h, s, v)

            # Adjust color components by a random amount
            h = self.rand_change_colcomp(h, self.options['huestep_max'], base_h, self.options['huediff_max'])
            s = self.rand_change_colcomp(s, self.options['satstep_max'], base_s, self.options['satdiff_max'])
            v = self.rand_change_colcomp(v, self.options['valstep_max'], base_v, self.options['valdiff_max'])

            (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
            #log.debug("r g b: %f %f %f", r, g, b)
            self.hol.setglobe(idx, int(255*r), int(255*g), int(255*b))
            pass
        pass
    
    def twinkle(self):
        """
        Change globe colours using some algorithm
        """
        for idx in range(0, self.hol.NUM_GLOBES):


            if self.options['twinkle_algo'] == 'simplex':
                self.twinkle_simplex(idx)
                pass
            
            elif self.options['twinkle_algo'] == 'random_limits':
                self.twinkle_random_limits(idx)
                pass

            # No globe colour updates, just chase
            elif self.options['twinkle_algo'] == 'chase_only':
                pass
            
            else:
                self.twinkle_random_shift(idx)
                pass
            pass

        # Chase enabled?
        if self.options['chase'] is not None:
            self.hol.chase(self.options['chase'])
            pass
        
        self.hol.render()
        pass

class TwinkleApp(ButtonApp):

    def start(self):
        self.t = TwinkleThread()
        self.modenum = 0
        self.t.set_mode(self.modenum)
        self.t.start()

    def stop(self):
        self.t.terminate = True

    def up(self):
        self.modenum += 1
        if self.modenum > len(MODES)-1:
            self.modenum = 0
            pass
        self.t.set_mode(self.modenum)
        pass

    def down(self):
        self.modenum -= 1
        if self.modenum < 0:
            self.modenum = len(MODES)-1
            pass
        self.t.set_mode(self.modenum)
        pass

class TwinkleThread(threading.Thread):
    """
    Singleton thread that runs the animation
    """
    def run(self):
        self.terminate = False
        
        self.hol = ButtonHoliday()
        self.modenum = 0
        self.twinkler = Twinkler(self.hol, MODES[self.modenum])

        while True:
            if self.terminate:
                return
            
            self.twinkler.twinkle()
            time.sleep(MODES[self.modenum]['snoozetime'])
            pass
        pass

    def set_mode(self, modenum):
        self.modenum = modenum
        if hasattr(self, 'twinkler'):
            self.twinkler.options = MODES[modenum]

            # Reset the initialisation pattern
            self.twinkler.set_pattern(MODES[modenum]['init_pattern'])
            pass
        pass
    pass
    
if __name__ == '__main__':
    app = TwinkleApp()
    app.start()
    time.sleep(1)
    app.down()
    time.sleep(1)
    app.up()    
    time.sleep(1)
    
    for i in range(len(MODES)-1):
        app.up()
        print "running in mode", app.modenum
        time.sleep(2)
        pass

    app.up()
    print "running in mode", app.modenum
    time.sleep(2)
    
    app.stop()
