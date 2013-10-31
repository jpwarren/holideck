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

from secretapi.holidaysecretapi import HolidaySecretAPI

# FIXME: replace with OptionParser options
# Height of display == number of globes in Holiday strings
DISPLAY_HEIGHT = HolidaySecretAPI.NUM_GLOBES

# Width of display == number of strings we want to use
DEFAULT_WIDTH = 10

def image_to_globes(img, width=DEFAULT_WIDTH, height=DISPLAY_HEIGHT):
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
    
    for w_slice in range(width):
        globelist = []
        for h_slice in range(height):
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
        if not self.options.imgfile and len(self.args) == 0:
            self.error("Image filename not given.")
            pass

        if not self.options.imgfile:
            self.options.imgfile = self.args[0]
            pass
        pass

def render_image(img, hols, width, height, switchback=None):
    """
    Render an image to a set of remote Holidays

    @param switchback: How many globes per piece of a switchback
    """
    globelists = image_to_globes(img, width, height)

    # Using this indirect array method, rather than set_globes()
    # directly, because some weird bug I can't find and squash makes the
    # globelists all the same if we try to render the Holidays in one
    # go, rather than rendering each 'line' of the switchback.
    # Your guess is as good as mine.
    holglobes = []
    for i in range(len(hols)):
        holglobes.append( [[0x00,0x00,0x00]] * HolidaySecretAPI.NUM_GLOBES )
        pass
    
    # If switchback mode is enabled, reverse order
    # of every second line, so they display the right
    # way on zigzag Holidays
    pieces = int(math.floor(float(HolidaySecretAPI.NUM_GLOBES) / height))

    for l, line in enumerate(globelists):
        # swap order every second line if in switchback mode
        # Which holiday are we talking to?
        holid = l*height / (pieces * switchback)
        hol = hols[holid]
        
        #print "holid %d, l %d, oddeven %d, l mod pieces %d" % (holid, l, (l % (pieces)) % 2, l % (pieces))
        basenum = (l%pieces) * height

        for i, values in enumerate(line):
            r, g, b = values
            if not (l % pieces) % 2:
                globe_idx = basenum + i
            else:
                globe_idx = basenum + (height-i) - 1
                pass
            holglobes[holid][globe_idx] = [r,g,b]
            #hol.setglobe(globe_idx, r, g, b)
            pass
        pass

    # Render to each Holiday
    for i, hol in enumerate(hols):
        hol.set_pattern( holglobes[i] )
        hol.render()
        pass
    pass

    
if __name__ == '__main__':

    usage = "Usage: %prog [options] <filename>"
    optparse = HoliscreenOptions(usage=usage)
    options, args = optparse.parseOptions()
    hols = []
    for i in range(options.numstrings):
        hols.append(HolidaySecretAPI(port=options.portstart+i))
        pass

    img = Image.open(options.imgfile)

    # FIXME: Swap height and width for horizontal orientation
    if options.switchback:
        height = options.switchback
        pieces = int(math.floor(float(HolidaySecretAPI.NUM_GLOBES) / height))
        width = options.numstrings * pieces
    else:
        height = HolidaySecretAPI.NUM_GLOBES
        pieces = options.numstrings
        width = options.numstrings
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
        render_image(img, hols, width, height, options.switchback)
        while True:
            # get the next frame after a short delay
            time.sleep(options.anim_sleep)
            
            try:
                img.seek(img.tell()+1)
                render_image(img, hols, width, height, options.switchback)
            except EOFError:
                img.seek(0)
                render_image(img, hols, width, height, options.switchback)
                pass
            pass
        pass
    else:
        render_image(img, hols, width, height, options.switchback)
        pass
