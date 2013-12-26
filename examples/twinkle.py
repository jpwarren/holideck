#!/usr/bin/python
"""
Twinkling pretty lights on the Holiday tree
"""

import optparse
import time
import sys
import random
import colorsys
import webcolors

import json

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
        
        self.add_option('-f', '--patternfile', dest='patternfile',
                        help="Initalise string with a pattern from a JSON format file",
                        type="string")

        self.add_option('', '--chase', dest='chase',
                        help="Lights chase around the string",
                        action="store_true", default=False)

        self.add_option('', '--chase-direction', dest='chase_direction',
                        help="Set direction of chase, if chase enabled [%default]",
                        type="choice", choices=['forward', 'backward'], default='forward')
        
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
        (r, g, b) = basecolor
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
    
def twinkle_holiday(hol,
                    huestep_max=0.1,
                    satstep_max=0.1,
                    valstep_max=0.5,
                    huediff_max=1.0,
                    satdiff_max=1.0,
                    valdiff_max=1.0,
                    change_chance=1.0,
                    basecolor=None,
                    chase=False,
                    chase_direction='forward',
                    ):
    """
    Make a Holiday twinkle like the stars
    """
    # For each globe, mostly have a random drift of brightness
    # and hue by but occasionally jump in brightness up or down
    if basecolor:
        (base_r, base_g, base_b) = basecolor
        base_hsv = colorsys.rgb_to_hsv(base_r/255.0, base_g/255.0, base_b/255.0)
    
    for idx in range(0, HolidaySecretAPI.NUM_GLOBES):

        # % chance of updating a given globe
        if random.random() < change_chance:
        
            r, g, b = hol.getglobe(idx)
            (h, s, v) = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            #log.debug("start h s v: %f %f %f", h, s, v)
            # Adjust hue by a random amount
            huestep = random.random() * huestep_max
            # 50% chance of positive or negative step
            if random.randint(0, 1):
                h += huestep
                if basecolor and abs(base_hsv[0] - h) > huediff_max:
                    h = base_hsv[0] + huediff_max
                if h > 1.0:
                    h = h - 1.0
            else:
                h -= huestep
                if basecolor and abs(h - base_hsv[0]) > huediff_max:
                    h = base_hsv[0] - huediff_max

                if h < 0.0:
                    h = 1.0 + h
                pass

            satstep = random.random() * satstep_max
            if random.randint(0, 1):
                s += satstep
                if basecolor and abs(base_hsv[1] - s) > satdiff_max:
                    s = base_hsv[1] + satdiff_max

                if s > 1.0:
                    s = 1.0
            else:
                s -= satstep
                if basecolor and abs(s - base_hsv[1]) > satdiff_max:
                    s = base_hsv[1] - satdiff_max

                # Make sure things stay bright and colorful!
                if s < 0.0:
                    s = 0.0

            # Adjust value by a random amount
            valstep = random.random() * valstep_max
            # 50% chance of positive or negative step
            if random.randint(0, 1):
                v += valstep
                if basecolor and abs(base_hsv[2] - v) > valdiff_max:
                    v = base_hsv[2] + valdiff_max

                if v > 1.0:
                    v = 1.0
            else:
                v -= valstep
                if basecolor and abs(v - base_hsv[2]) > valdiff_max:
                    v = base_hsv[2] - valdiff_max

                if v < 0.2:
                    v = 0.2
                pass

            #log.debug("end h s v: %f %f %f", h, s, v)

            (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
            #log.debug("r g b: %f %f %f", r, g, b)
            hol.setglobe(idx, int(255*r), int(255*g), int(255*b))
            pass
        pass

    # Chase mode?
    if chase:
        if chase_direction == 'forward':
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

    if options.basecolor is not None:
        basecolor = webcolors.hex_to_rgb(options.basecolor)
    else:
        basecolor = None
    
    hols = []
    if len(args) > 1:
        for arg in args:
            hol_addr, hol_port = arg.split(':')
            hols.append(HolidaySecretAPI(addr=hol_addr, port=int(hol_port)))
    else:
        hol_addr, hol_port = args[0].split(':')
        for i in range(options.numstrings):
            hols.append(HolidaySecretAPI(addr=hol_addr, port=int(hol_port)+i))
            pass

    for hol in hols:
        init_hol(hol, basecolor, options.initpattern)
        pass
    
    while True:
        for hol in hols:
            twinkle_holiday(hol,
                            options.huestep_max,
                            options.satstep_max,
                            options.valstep_max,
                            options.huediff_max,
                            options.satdiff_max,
                            options.valdiff_max,
                            options.change_chance,
                            basecolor,
                            options.chase,
                            options.chase_direction)
            pass
        time.sleep(options.anim_sleep)

