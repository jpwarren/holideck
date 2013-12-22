#!/usr/bin/python
"""
A simple hack to turn one or more Holidays into an LED scrolling display
"""

import optparse
import time
import pygame
import sys
import math

from secretapi.holidaysecretapi import HolidaySecretAPI

from holiscreen import render_to_hols

# Initialise the font module
pygame.font.init()

class LEDScrollerOptions(optparse.OptionParser):
    """
    Command-line options parser
    """
    def __init__(self, *args, **kwargs):
        optparse.OptionParser.__init__(self, **kwargs)
        self.addOptions()

    def addOptions(self):
        self.add_option('-n', '--numstrings', dest='numstrings',
                        help="Number of Holiday strings to simulate [%default]",
                        type="int", default=7)

        self.add_option('-a', '--animate', dest='animate',
                        help="Run in scroller mode",
                        action="store_true" )

        self.add_option('-s', '--sleeptime', dest='anim_sleep',
                        help="Sleep between animation frames, in seconds [%default]",
                        type="float", default=0.1 )
        
        # Listen on multiple TCP/UDP ports, one for each Holiday we simulate
        self.add_option('-p', '--portstart', dest='portstart',
                        help="Port number to start at for UDP listeners [%default]",
                        type="int", default=9988)

        self.add_option('', '--switchback', dest='switchback',
                        help="'Switchback' strings, make a single string display like its "
                        "more than one every SWITCHBACK globes",
                        type="int")

        self.add_option('', '--font', dest='fontname',
                        help="Name of the font to use. [%default]",
                        type="string", default="couriernew")

        self.add_option('', '--antialias', dest='antialias',
                        help="Use anti-aliasing for font rendering. [%default]",
                        action="store_true", default=False)
        
        self.add_option('', '--fontsize', dest='fontsize',
                        help="Size of the font, in pixels [%default]",
                        type="int", default="7")

        self.add_option('', '--color', dest='color',
                        help="Color of the font [%default]",
                        type="string", default="0xffffff")
        
        self.add_option('', '--list-fonts', dest='listfonts',
                        help="List fonts available for use",
                        action="store_true")

        self.add_option('', '--blank-padding', dest='blankpadding',
                        help="Spaces to leave between end of string "
                        "and start when wrapping around. [%default]",
                        type="int", default=2)
        
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

def text_to_globes(text, width, height,
                   color=(255,255,255),
                   offset_left=0):
    """
    Take a text string and return a list of globelists.

    One list will be returned for vertical line, each of width globes
    long. This implies Holidays layed out horizontally for display.

    #FIXME: Allow rotation for horizontal display with vertically hung
    Holidays.

    The left offset can be set (in pixels), which will control the
    window of the text display. Incrementing the offset can be used
    to create a scrolling display.
    """
    #font = pygame.font.SysFont("None", 10)

    font = pygame.font.SysFont(options.fontname, options.fontsize)
    color = pygame.Color(color)

    surface = font.render(text, options.antialias, color, (0,0,0) )

    globelists = []

    # Now fetch the pixels as an array
    pa = pygame.PixelArray(surface)
    for i in range(len(pa[0])):
        globes = []
        pixels = pa[:,i]
        pixvals = [ pa.surface.unmap_rgb(x) for x in pixels ]
        # Check to see if this is a blank line, i.e.
        # all pixels are black. Ignore the line if this is the case.
        # We don't want to waste lines on blanks.
        if pixvals == [ (0,0,0,255) ] * len(pixvals):
            #print "skipping blank line %d" % i
            continue
        
        for (r, g, b, a) in pixvals:
            # Convert from a surface color int to RGBA values
            globes.append( (r,g,b) )
            pass

        # Pad with blanks if the text is shorter than width
        if len(pa) < width:
            globes.extend( [(0,0,0)] * (width - len(pa)) )
            pass
        globelists.append(globes)            
        pass
    return globelists

if __name__ == '__main__':

    usage = "Usage: %prog [options] <hol_addr:hol_port> [<hol_addr:hol_port> ... ]"
    optparse = LEDScrollerOptions(usage=usage)

    options, args = optparse.parseOptions()
    
    if options.switchback:
        width = options.switchback
        pieces = int(math.floor(float(HolidaySecretAPI.NUM_GLOBES) / width))        
        height = pieces * options.numstrings
    else:
        height = options.numstrings
        width = HolidaySecretAPI.NUM_GLOBES

    if options.listfonts:
        print '\n'.join(pygame.font.get_fonts())
        sys.exit(0)

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

    # The text to render is passed in from stdin
    text = sys.stdin.read().rstrip()
    if len(text) == 0:
        text = "Holiday by MooresCloud. The world's most intelligent Christmas lights!"
        pass
    text = ''.join([text, ' ' * options.blankpadding])

    glist = text_to_globes(text, width, height, color=options.color)

    #print "glist:", glist
    # Scroll the display
    offset = 0
    while True:
        # Draw only as much of the globelists as will fit in the width
        render_glist = []
        for hol_list in glist:
            new_list = hol_list[offset:width+offset]

            # FIXME: Ability to scroll in both directions, via a flag
            # wraparound
            if len(new_list) < width:
                new_list.extend(hol_list[:(width-len(new_list))])
                pass
            render_glist.append(new_list)
            pass
        #print "renderlist:", render_glist
        render_to_hols(render_glist, hols, width, height,
                       orientation='horizontal',
                       switchback=options.switchback)
        offset += 1
        if offset > len(glist[0]):
            offset = 0
            pass

        if not options.animate:
            sys.exit(0)
        time.sleep(options.anim_sleep)

