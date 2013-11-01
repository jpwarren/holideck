#!/usr/bin/python
"""
A simple hack to turn one or more Holidays into an LED scrolling display
"""

import optparse
import time
import pygame
import sys

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
                        "more than one every m globes",
                        type="int")

        self.add_option('', '--font', dest='fontname',
                        help="Name of the font to use. [%default]",
                        type="string", default="couriernew")

        self.add_option('', '--fontsize', dest='fontsize',
                        help="Size of the font, in points [%default]",
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
        pass

def to_rgb( norm_rgba, mask=(0,0,0) ):
    """
    Convert normalized RGBA color to flat RGB color.

    Default is for a black background.
    Annoyingly, pygame doesn't seem to have this feature in its
    Color module for some reason. Sadface.
    """
    #print norm_rgba
    r, g, b, a = norm_rgba
    bg_r, bg_g, bg_b = mask

    # Convert to target color
    # http://stackoverflow.com/questions/2049230/convert-rgba-color-to-rgb
    tr = int((((1-a)*r) + (a*bg_r)) * 255)
    tg = int((((1-a)*g) + (a*bg_g)) * 255)
    tb = int((((1-a)*b) + (a*bg_b)) * 255)

    return (tr, tg, tb)
    
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

    surface = font.render(text, True, color, (0,0,0) )
    globelists = []

    # Now fetch the pixels as an array
    pa = pygame.PixelArray(surface)
    for i in range(min(height, len(pa[0]))):
        globes = []

        # First, grab the pixels in the window
        pixels = pa[:,i]
        for px in pixels:

            # Convert from a surface color int to RGBA values
            (r,g,b,a) = pa.surface.unmap_rgb(px)
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

    usage = "Usage: %prog [options]"
    optparse = LEDScrollerOptions(usage=usage)

    options, args = optparse.parseOptions()

    height = options.numstrings
    
    if options.switchback:
        width = options.switchback
    else:
        width = HolidaySecretAPI.NUM_GLOBES

    if options.listfonts:
        print '\n'.join(pygame.font.get_fonts())
        sys.exit(0)

    hols = []
    for i in range(options.numstrings):
        hols.append(HolidaySecretAPI(port=options.portstart+i))
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
            # wraparound
            if len(new_list) < width:
                new_list.extend(hol_list[:(width-len(new_list))])
                pass
            render_glist.append(new_list)
            pass
        #print "renderlist:", render_glist
        render_to_hols(render_glist, hols, width, height, orientation='horizontal')
        offset += 1
        if offset > len(glist[0]):
            offset = 0
            pass
        time.sleep(options.anim_sleep)
