#!/usr/bin/python
"""
Twinkling pretty lights on the Holiday tree
"""

import optparse
import time
import sys
import random
import colorsys

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
                
        # Send on multiple TCP/UDP ports, one for each Holiday we simulate
        self.add_option('-p', '--portstart', dest='portstart',
                        help="Port number to start at for UDP listeners [%default]",
                        type="int", default=9988)

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
        pass

def init_hol(hol):
    """
    Initialize a Holiday to some random-ish colors
    """
    for globeidx in range(0, HolidaySecretAPI.NUM_GLOBES):
        color = []
        for i in range(0, 3):
            color.append(random.randint(0, 255))
            pass
        r, g, b = color
        hol.setglobe(globeidx, r, g, b)
        pass
    hol.render()
    
def twinkle_holiday(hol,
                    huestep_max=0.1,
                    satstep_max=0.1,
                    valstep_max=0.5,
                    change_chance=1.0
                    ):
    """
    Make a Holiday twinkle like the stars
    """
    # For each globe, mostly have a random drift of brightness
    # and hue by but occasionally jump in brightness up or down
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
                if h > 1.0:
                    h = h - 1.0
            else:
                h -= huestep
                if h < 0.0:
                    h = 1.0 + h
                pass

            satstep = random.random() * satstep_max
            if random.randint(0, 1):
                s += satstep
                if s > 1.0:
                    s = 1.0
            else:
                s -= satstep
                # Make sure things stay bright and colorful!
                if s < 0.5:
                    s = 0.5

            # Adjust value by a random amount
            valstep = random.random() * valstep_max
            # 50% chance of positive or negative step
            if random.randint(0, 1):
                v += valstep
                if v > 1.0:
                    v = 1.0
            else:
                v -= valstep
                if v < 0.0:
                    v = 0.0
                pass

            #log.debug("end h s v: %f %f %f", h, s, v)

            (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
            #log.debug("r g b: %f %f %f", r, g, b)
            hol.setglobe(idx, int(255*r), int(255*g), int(255*b))
            pass
        pass
    hol.render()
    
if __name__ == '__main__':

    usage = "Usage: %prog [options] <hol_addr:hol_port> [<hol_addr:hol_port> ... ]"
    optparse = TwinkleOptions(usage=usage)

    options, args = optparse.parseOptions()
    
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
        init_hol(hol)
        pass
    
    while True:
        for hol in hols:
            twinkle_holiday(hol,
                            options.huestep_max,
                            options.satstep_max,
                            options.valstep_max,
                            options.change_chance)
            pass
        time.sleep(options.anim_sleep)

