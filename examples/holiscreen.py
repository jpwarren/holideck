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

from secretapi.holidaysecretapi import HolidaySecretAPI

# FIXME: replace with OptionParser options
# Height of display == number of globes in Holiday strings
DISPLAY_HEIGHT = HolidaySecretAPI.NUM_GLOBES

# Width of display == number of strings we want to use
DEFAULT_WIDTH = 10

def image_to_globes(img, numstrings=DEFAULT_WIDTH):
    """
    Convert an image file into a Holiday string display

    @param imgfile: the image file to use
    @param numstring: the number of Holiday strings in the display
    """
    img = img.convert('RGB')

    # Ensure we will the 'screen' by fixing the display height
    new_width = int(img.size[0] * (float(DISPLAY_HEIGHT) / img.size[1] ))
    img.thumbnail( (new_width, DISPLAY_HEIGHT), Image.ANTIALIAS)

    # Now we want to sample display_width times across the width of
    # the image
    stringlist = []
    width, height = img.size

    slice_width = float(width)/float(numstrings)
    for piece in range(numstrings):
        # top left is (piece * slice_width, 0)
        # bottom right is (piece+1 * offset, height)
        bbox = ( int(piece * slice_width), 0,
                int(math.ceil((piece+1) * slice_width)), height)
        region = img.crop(bbox)
        pixeldata = region.load()

        # For this region, average all the points at each Y,
        # and save them as a list of colour values for the string
        globelist = []
        for y in xrange(region.size[1]):
            r = g = b = 0
            for x in xrange(region.size[0]):
                # This works even for PNG images with alpha values
                tr, tg, tb = pixeldata[x, y]
                r += tr
                g += tg
                b += tb
                pass

            # Take average of pixels
            #print "r, g, b, rg", r, g, b, region.size[0]
            globelist.append((int(r/float(region.size[0])),
                              int(g/float(region.size[0])),
                              int(b/float(region.size[0])),
                              ))
            pass

        # save the list of globe colours
        # We reverse, because otherwise the display is upside-down
        globelist.reverse()
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

def render_image(img, hols):
    """
    Render an image to a set of remote Holidays
    """
    globelists = image_to_globes(img,
                                 options.numstrings)

    for hol, globelist in zip(hols, globelists):
        for i in range(len(globelist)):
            r, g, b = globelist[i]
            hol.setglobe(i, r, g, b)
            pass
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
        render_image(img, hols)
        while True:
            # get the next frame after a short delay
            time.sleep(options.anim_sleep)
            
            try:
                img.seek(img.tell()+1)
                render_image(img, hols)
            except EOFError:
                img.seek(0)
                render_image(img, hols)
                pass
            pass
        pass
    else:
        render_image(img, hols)
        pass
    
