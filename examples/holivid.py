#!/usr/bin/python
"""
Display video on a set of Holidays
"""
import numpy as np
import cv2
import math
import optparse

from api.udpholiday import UDPHoliday
from holiscreen import render_to_hols

NUM_GLOBES = UDPHoliday.NUM_GLOBES

class HolividOptions(optparse.OptionParser):
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

        self.add_option('-f', '--file', dest='filename',
                        help="Video file to display.",
                        type="string" )

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

        self.add_option('', '--fps', dest='fps',
                        help="Set video playback frames-per-second. [%default]",
                        type="int", default=25)

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

        if not self.options.filename:
            self.error("Video filename not given.")
            pass
        pass

if __name__ == '__main__':

    usage = "Usage: %prog [options] <hol_addr:hol_port> [<hol_addr:hol_port> ... ]"
    optparse = HolividOptions(usage=usage)
    options, args = optparse.parseOptions()
    
    hols = []
    if len(args) > 1:
        for arg in args:
            hol_addr, hol_port = arg.split(':')
            hols.append(UDPHoliday(ipaddr=hol_addr, port=int(hol_port)))
    else:
        hol_addr, hol_port = args[0].split(':')
        for i in range(options.numstrings):
            hols.append(UDPHoliday(ipaddr=hol_addr, port=int(hol_port)+i))
            pass
        pass

    if options.switchback:
        if options.orientation == 'vertical':
            height = options.switchback
            pieces = int(math.floor(float(NUM_GLOBES) / height))
            width = options.numstrings * pieces
        else:
            width = options.switchback
            pieces = int(math.floor(float(NUM_GLOBES) / width))
            height = options.numstrings * pieces
    else:
        if options.orientation == 'vertical':
            height = NUM_GLOBES
            pieces = options.numstrings
            width = options.numstrings
        else:
            width = NUM_GLOBES
            pieces = options.numstrings
            height = options.numstrings
            pass
        pass
    
    cap = cv2.VideoCapture(options.filename)
    newsize = (width, height)

    skipframe = False
    
    while True:
        ret, frame = cap.read()

        if ret != True:
            print "No valid frame."
            break

        # Resize the frame into the resolution of our Holiday array
        frame = cv2.resize(frame, newsize, interpolation=cv2.INTER_AREA)

        # The colours are in the wrong format, so convert them
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        #cv2.imshow('frame', frame)

        # A frame is just a Numpy array of pixel values, i.e. globelists. We need to take
        # these values and map them onto our holiday array.
        render_to_hols(frame, hols, width, height,
                       options.orientation, options.switchback)

        # Wait period between keycapture (in milliseconds)
        # This gives us approximately the right number of frames per second
        wait_time = int(1000/options.fps)
        if cv2.waitKey(wait_time) & 0xFF == ord('q'):
            break
        pass

    cap.release()
    cv2.destroyAllWindows()

