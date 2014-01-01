#!/usr/bin/python
"""
Twinkling pretty lights on the Holiday
"""

import optparse
import time
import sys
import random
import colorsys
import webcolors
import json

from simplexnoise import raw_noise_2d

from secretapi.holidaysecretapi import HolidaySecretAPI

import logging
log = logging.getLogger(sys.argv[0])
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s: %(name)s [%(levelname)s]: %(message)s"))
log.addHandler(handler)
log.setLevel(logging.DEBUG)

class TwinkleOptions(optparse.OptionParser):
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

        self.add_option('-b', '--basecolor', dest='basecolor',
                        help="Color to initialize string to, as #nnnnnn",
                        type="string")
        
        self.add_option('-c', '--change_chance', dest='change_chance',
                        help="% chance a given globe will change each round [%default]",
                        type="float", default=1.0 )
        
        self.add_option('-a', '--animsleep', dest='anim_sleep',
                        help="Sleep between animation frames, in seconds [%default]",
                        type="float", default=0.1 )

        self.add_option('-f', '--patternfile', dest='patternfile',
                        help="Initalise string with a pattern from a JSON format file",
                        type="string")

        self.add_option('-t', '--twinkle-algo', dest='twinkle_algo',
                        help="Algorithm to use for twinkling [%default]",
                        type="choice", choices=['random', 'simplex'], default='random')
        
        self.add_option('-H', '--HUESTEP', dest='huestep_max',
                        help="Maximum step between hues [%default]",
                        type="float", default=0.1 )

        self.add_option('-S', '--SATSTEP', dest='satstep_max',
                        help="Maximum step between saturations [%default]",
                        type="float", default=0.01 )

        self.add_option('-V', '--VALSTEP', dest='valstep_max',
                        help="Maximum step between values [%default]",
                        type="float", default=0.2 )

        self.add_option('', '--huediff-max', dest='huediff_max',
                        help="Maximum hue difference from basecolor [%default]",
                        type="float", default=1.0 )

        self.add_option('', '--satdiff-max', dest='satdiff_max',
                        help="Maximum saturation difference from basecolor [%default]",
                        type="float", default=1.0 )

        self.add_option('', '--valdiff-max', dest='valdiff_max',
                        help="Maximum value difference from basecolor [%default]",
                        type="float", default=1.0 )
        
        self.add_option('', '--chase-forwards', dest='chase',
                        help="Lights chase around the string",
                        action="store_true")

        self.add_option('', '--chase-backwards', dest='chase',
                        help="Lights chase around the string",
                        action="store_false")
        
        self.add_option('', '--simplex-damper', dest='simplex_damper',
                        help="Amount of simplex noise dampening [%default]",
                        type="float", default=5.0)
        
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
            self.error("Specify address and port of remote Holiday(s)")
            pass

        self.options.initpattern = None
        if self.options.patternfile:
            with open(self.options.patternfile) as fp:
                jdata = json.load(fp)
                self.options.initpattern = jdata['lights']
                pass
        pass

def init_hol(hol, basecolor=None, pattern=None):
    """
    Initialize a Holiday to some random-ish colors
    """
    if basecolor is not None:
        (r, g, b) = webcolors.hex_to_rgb(basecolor)
        hol.fill(r, g, b)
    elif pattern is not None:
        for globeidx, vals in enumerate(pattern):
            (r, g, b) = webcolors.hex_to_rgb(vals)
            hol.setglobe(globeidx, r, g, b)
            pass
    else:
        for globeidx in range(0, HolidaySecretAPI.NUM_GLOBES):
            color = []
            # red
            color.append(random.randint(0, 130))
            #color.append(0)
            # green
            color.append(random.randint(0, 130))
            # blue
            color.append(random.randint(0, 130))
            #color.append(0)

            r, g, b = color

            hol.setglobe(globeidx, r, g, b)
            pass
    hol.render()

    pattern = hol.globes[:]
    return pattern
    
def twinkle_holiday(hol, options, init_pattern, noise_array=None):
    """
    Make a Holiday twinkle like the stars
    """
    # For each globe, mostly have a random drift of brightness
    # and hue by but occasionally jump in brightness up or down
    if options.basecolor:
        (base_r, base_g, base_b) = webcolors.hex_to_rgb(options.basecolor)
        base_hsv = colorsys.rgb_to_hsv(base_r/255.0, base_g/255.0, base_b/255.0)
        pass
    
    if noise_array is None:
        noise_array = [ 0, ] * HolidaySecretAPI.NUM_GLOBES
        pass
        
    for idx in range(0, HolidaySecretAPI.NUM_GLOBES):

        # Choose globe update algorithm
        if options.twinkle_algo == 'simplex':
            nv = raw_noise_2d(noise_array[idx], random.random()) / options.simplex_damper
            noise_array[idx] += nv
            if noise_array[idx] > 1.0:
                noise_array[idx] = 1.0
                pass
            elif noise_array[idx] < -1.0:
                noise_array[idx] = -1.0
                pass

            ranger = (noise_array[idx] + 1.0) / 2.0

            # Adjust colour. If basecolor, adjust from basecolor
            if options.basecolor:
                (base_r, base_g, base_b) = webcolors.hex_to_rgb(options.basecolor)
                r = int(base_r * ranger)
                g = int(base_g * ranger)
                b = int(base_b * ranger)
                pass
            else:
                # adjust from original color
                (base_r, base_g, base_b) = init_pattern[idx]
                #log.debug("adjusting from orig: %d %d %d", base_r, base_g, base_b)
                r = int(base_r * ranger)
                g = int(base_g * ranger)
                b = int(base_b * ranger)
                pass
            hol.setglobe(idx, r, g, b)
            
        else:
            # % chance of updating a given globe
            if random.random() < options.change_chance:

                r, g, b = hol.getglobe(idx)
                (h, s, v) = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                #log.debug("start h s v: %f %f %f", h, s, v)
                # Adjust hue by a random amount
                huestep = random.random() * options.huestep_max
                # 50% chance of positive or negative step
                if random.randint(0, 1):
                    h += huestep
                    if options.basecolor and abs(base_hsv[0] - h) > options.huediff_max:
                        h = base_hsv[0] + options.huediff_max
                    if h > 1.0:
                        h = h - 1.0
                else:
                    h -= huestep
                    if options.basecolor and abs(h - base_hsv[0]) > options.huediff_max:
                        h = base_hsv[0] - options.huediff_max

                    if h < 0.0:
                        h = 1.0 + h
                    pass

                satstep = random.random() * options.satstep_max
                if random.randint(0, 1):
                    s += satstep
                    if options.basecolor and abs(base_hsv[1] - s) > options.satdiff_max:
                        s = base_hsv[1] + options.satdiff_max

                    if s > 1.0:
                        s = 1.0
                else:
                    s -= satstep
                    if options.basecolor and abs(s - base_hsv[1]) > options.satdiff_max:
                        s = base_hsv[1] - options.satdiff_max

                    # Make sure things stay bright and colorful!
                    if s < 0.0:
                        s = 0.0

                # Adjust value by a random amount
                valstep = random.random() * options.valstep_max
                # 50% chance of positive or negative step
                if random.randint(0, 1):
                    v += valstep
                    if options.basecolor and abs(base_hsv[2] - v) > options.valdiff_max:
                        v = base_hsv[2] + options.valdiff_max

                    if v > 1.0:
                        v = 1.0
                else:
                    v -= valstep
                    if options.basecolor and abs(v - base_hsv[2]) > options.valdiff_max:
                        v = base_hsv[2] - options.valdiff_max

                    if v < 0.2:
                        v = 0.2
                    pass

                #log.debug("end h s v: %f %f %f", h, s, v)

                (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
                #log.debug("r g b: %f %f %f", r, g, b)
                hol.setglobe(idx, int(255*r), int(255*g), int(255*b))
                pass
            pass
        pass

    # Chase mode?
    if options.chase:
        if options.chase_direction:
            # Rotate all globes around by one place
            oldglobes = hol.globes[:]
            hol.globes = oldglobes[1:]
            hol.globes.append(oldglobes[0])
            pass
        else:
            log.debug("old: %s", hol.globes)
            oldglobes = hol.globes[:]
            hol.globes = oldglobes[:-1]
            hol.globes.insert(0, oldglobes[-1])
            log.debug("new: %s", hol.globes)
            pass
    
    hol.render()
    
if __name__ == '__main__':

    usage = "Usage: %prog [options] <hol_addr:hol_port> [<hol_addr:hol_port> ... ]"
    optparse = TwinkleOptions(usage=usage)

    options, args = optparse.parseOptions()

    hols = []
    # List of holiday initial patterns
    hol_inits = []

    # List of holiday noise patterns
    hol_noise = []
    if len(args) > 1:
        for arg in args:
            hol_addr, hol_port = arg.split(':')
            hols.append(HolidaySecretAPI(addr=hol_addr, port=int(hol_port)))
    else:
        hol_addr, hol_port = args[0].split(':')
        for i in range(options.numstrings):
            hols.append(HolidaySecretAPI(addr=hol_addr, port=int(hol_port)+i))
            pass

    # Initialise holidays
    for hol in hols:
        hol_inits.append(init_hol(hol, options.basecolor, options.initpattern))
        hol_noise.append(None)
        pass

    while True:
        for i, hol in enumerate(hols):
            noise = twinkle_holiday(hol, options, hol_inits[i], hol_noise[i])
            pass
        time.sleep(options.anim_sleep)

