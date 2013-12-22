#!/usr/bin/python
#
# Use a series of Holidays as a lo-res, flexible display screen that you
# can walk through like a beaded curtain.
#

# FIXME: Update to be able to do video.

import optparse
import Image
import math
import time
import numpy
import sys
import logging

from secretapi.holidaysecretapi import HolidaySecretAPI

# Height of display == number of globes in a string
DEFAULT_HEIGHT = HolidaySecretAPI.NUM_GLOBES

# Width of display == number of strings we want to use
DEFAULT_WIDTH = HolidaySecretAPI.NUM_GLOBES

log = logging.getLogger(sys.argv[0])
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s: %(name)s [%(levelname)s]: %(message)s"))
log.addHandler(handler)
log.setLevel(logging.DEBUG)

def image_to_globes(img, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    """
    Convert an image file into a Holiday string display

    @param imgfile: the image file to use
    @param numstring: the number of Holiday strings in the display
    """
    img = img.convert('RGB')

    # Resize image based on the longest side of our holiscreen
    if width < height:
        new_width = int(img.size[0] * (float(height) / img.size[1] ))
        new_height = height
    else:
        new_width = width
        new_height = int(img.size[0] * (float(width) / img.size[1] ))

    img.thumbnail( (new_width, new_height), Image.ANTIALIAS)

    # Now we want to sample display_width times across the width of
    # the image
    stringlist = []
    iw, ih = img.size

    slice_width = float(iw)/float(width)
    slice_height = float(ih)/float(height)

    # Slice image into boxed partitions slice_width x slice_height
    # and average the colour of the pixels in that box to give
    # us the pixel colour for our downsampled display.
    # FIXME: There's probably a function in PIL to do this, but
    # I haven't been able to find it yet.
    for h_slice in range(height):    
        globelist = []
        for w_slice in range(width):
            bbox = ( int(w_slice * slice_width),
                     int(h_slice * slice_height),
                     int(math.ceil((w_slice+1) * slice_width)),
                     int(math.ceil((h_slice+1) * slice_height))
                     )
            region = img.crop(bbox)
            pixeldata = list(region.getdata())

            # split out the r, b, g values for each pixel and average them
            rlist, glist, blist = zip(*pixeldata)
            globelist.append( (int(numpy.average(rlist)),
                               int(numpy.average(glist)),
                               int(numpy.average(blist)),)
                              )
            pass
        # save the list of globe colours
        # We reverse, because otherwise the display is upside-down
        #globelist.reverse()
        stringlist.append(globelist)
        pass
    return stringlist

class HoliscreenOptions(optparse.OptionParser):
    """
    Command-line options parser
    """
    def __init__(self, *args, **kwargs):
        optparse.OptionParser.__init__(self, **kwargs)
        self.addOptions()

    def addOptions(self):
        self.add_option('-n', '--numstrings', dest='numstrings',
                        help="Number of Holiday strings to simulate [%default]",
                        type="int", default=25)

        self.add_option('-f', '--file', dest='imgfile',
                        help="Image file to process. Overrides arguments.",
                        type="string" )

        self.add_option('-a', '--animate', dest='animate',
                        help="Run in animation mode. Required animated GIF.",
                        action="store_true" )

        self.add_option('-s', '--sleeptime', dest='anim_sleep',
                        help="Sleep between animation frames, in seconds [%default]",
                        type="float", default=0.1 )

        
        # Listen on multiple TCP/UDP ports, one for each Holiday we simulate
        self.add_option('-p', '--portstart', dest='portstart',
                        help="Port number to start at for UDP listeners [%default]",
                        type="int", default=9988)

        self.add_option('-o', '--orientation', dest='orientation',
                        help="Orientation of the strings [%default]",
                        type="choice", choices=['vertical', 'horizontal'], default='vertical')
        
        self.add_option('', '--switchback', dest='switchback',
                        help="'Switchback' strings, make a single string display like its "
                        "more than one every m globes",
                        type="int")
        pass


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

        if not self.options.imgfile:
            self.error("Image filename not given.")
            pass
        pass

def render_image(img, hols, width, height,
                 orientation='vertical',
                 switchback=None):
    """
    Render an image to a set of remote Holidays

    @param switchback: How many globes per piece of a switchback
    """
    #log.debug("w x h: %d x %d", width, height)
    globelists = image_to_globes(img, width, height)
    #log.debug("len globelists: %d", len(globelists))
    render_to_hols(globelists, hols, width, height, orientation, switchback)

def render_to_hols(globelists, hols, width, height,
                   orientation='vertical', switchback=None):
    """
    Render a set of globe values to a set of Holidays
    """
    # Using this indirect array method, rather than set_globes()
    # directly, because some weird bug I can't find and squash makes the
    # globelists all the same if we try to render the Holidays in one
    # go, rather than rendering each 'line' of the switchback.
    # Your guess is as good as mine.
    holglobes = []
    for i in range(len(hols)):
        holglobes.append( [[0x00,0x00,0x00]] * HolidaySecretAPI.NUM_GLOBES )
        pass

    if orientation == 'vertical':
        orientsize = height
    else:
        orientsize = width
    
    # If switchback mode is enabled, reverse order
    # of every second line, so they display the right
    # way on zigzag Holidays
    pieces = int(math.floor(float(HolidaySecretAPI.NUM_GLOBES) / orientsize))

    # The globelist is a set of y values. List [0] is all the vertical globes
    # for x = 0, list [1] is the vertical x=1 globes, etc.
    # The orientation determines which holiday gets each pixel in the list.
    # In vertical orientation, the first list goes to holiday 0, the second
    # to holiday 2. In switchback mode, the first n lists go to holiday 0.
    # In horizontal mode, the first row is spread between holidays, depending
    # on switchback.
    #log.debug("globelist len: %d", len(globelists))
    for l, line in enumerate(globelists):
            
        for i, values in enumerate(line):
            r, g, b = values

            #log.debug("os: %d, pieces: %d, sb: %s, l: %d, i: %d", orientsize, pieces, switchback, l, i)

            # Which holiday are we talking to?
            if orientation == 'horizontal':
                basenum = (l%pieces) * orientsize

                if switchback:
                    holid = l*orientsize / (pieces * switchback)
                else:
                    holid = l
                
                if not (l % pieces) % 2:
                    globe_idx = basenum + i
                else:
                    globe_idx = basenum + (orientsize-i) - 1
                    pass

            else:
                basenum = (i % pieces) * orientsize

                if switchback:
                    holid = i / pieces
                    #log.debug("basenum: %d", basenum)
                else:
                    holid = i
                    basenum = 0
                    
                if not (i % pieces) % 2:
                    globe_idx = basenum + l
                else:
                    globe_idx = basenum + (orientsize-l) - 1
                    pass
                
            try:
                #log.debug("holid: %d, globeidx: %d", holid, globe_idx)
                hol = hols[holid]
            except IndexError:
                log.error("Not enough Holidays for number of screen lines. Need at least %d." % (holid+1,))
                sys.exit(1)

            try:
                holglobes[holid][globe_idx] = [r,g,b]
            except IndexError:
                log.debug("Error at holid %d, globeidx %d", holid, globe_idx)
                raise

            #print "line: %d, holid: %d, globe: %d, val: (%d, %d, %d)" % (l, holid, globe_idx, r,g,b)

            pass
        pass

    # Render to each Holiday
    for i, hol in enumerate(hols):
        hol.set_pattern( holglobes[i] )
        hol.render()
        pass
    pass

    
if __name__ == '__main__':

    usage = "Usage: %prog [options] <hol_addr:hol_port> [<hol_addr:hol_port> ... ]"
    optparse = HoliscreenOptions(usage=usage)
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
        pass
    
    img = Image.open(options.imgfile)

    if options.switchback:
        if options.orientation == 'vertical':
            height = options.switchback
            pieces = int(math.floor(float(HolidaySecretAPI.NUM_GLOBES) / height))
            width = options.numstrings * pieces
        else:
            width = options.switchback
            pieces = int(math.floor(float(HolidaySecretAPI.NUM_GLOBES) / width))
            height = options.numstrings * pieces
    else:
        if options.orientation == 'vertical':
            height = HolidaySecretAPI.NUM_GLOBES
            pieces = options.numstrings
            width = options.numstrings
        else:
            width = HolidaySecretAPI.NUM_GLOBES
            pieces = options.numstrings
            height = options.numstrings
            pass
        pass

    isanimated = False

    # Detect animated GIFs
    if img.format == 'GIF':
        try:
            img.seek(img.tell()+1)
            isanimated = True
        except EOFError:
            img.seek(0)
            pass
        pass

    if isanimated and options.animate:
        # render first frame
        render_image(img, hols, width, height, options.orientation, options.switchback)
        while True:
            # get the next frame after a short delay
            time.sleep(options.anim_sleep)
            try:
                img.seek(img.tell()+1)

            except EOFError:
                img.seek(0)
                pass
            render_image(img, hols, width, height, options.orientation, options.switchback)
            pass
        pass
    else:
        render_image(img, hols, width, height, options.orientation, options.switchback)
        pass
