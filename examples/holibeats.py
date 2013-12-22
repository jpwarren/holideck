#!/usr/bin/python
#
# A SoundLevel monitor on a Holiday for sound playing on your PC
#
import sys
import pyaudio
import audioop
import math
import numpy
import scipy
import time
import datetime
#from scipy.signal import kaiserord, lfilter, firwin, freqz

from scipy import fft

import optparse

from secretapi.holidaysecretapi import HolidaySecretAPI

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
BUFSIZE = 2048

import logging
log = logging.getLogger(sys.argv[0])
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s: %(name)s [%(levelname)s]: %(message)s"))
log.addHandler(handler)
log.setLevel(logging.DEBUG)


def list_devices():
    # List all audio input devices
    p = pyaudio.PyAudio()
    i = 0
    n = p.get_device_count()

    for i in range(0, n):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print "Found device: %d: %s" % (i, dev['name'])
            i += 1
            pass
        pass
    pass

def get_default_device_id():
    """
    Find the default audio device we want to monitor
    """
    for i in range(0, n):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print "Found device: %d: %s" % (i, dev['name'])
            i += 1
            pass
        pass
    pass

def calc_samp_amp(sample):
    """
    Figure out the sample value to use for our spectrum
    analyser output for the given pre-filtered sample
    """
    SCALE_FACTOR = 10e4
    #result = numpy.std(sample) * SCALE_FACTOR
    result = max(abs(sample)) * SCALE_FACTOR
    
    return result

def send_blinken(hols, visdata, pieces=1,
                 switchback=None,
                 maxval=None,
                 maxheight=None,
                 autorange=True):
    """
    Create a light pattern for a remote Holidays
    based on the values we receive.

    If maxval is supplied, scale values as proportion of
    maxval, so the display auto-ranges.
    """
    #log.debug("numhols: %d, buckets: %d", len(hols), len(visdata))
    #log.debug("pieces: %d, sb: %d", pieces, switchback)

    # Same bug as in holiscreen.py render_to_hols()
    holglobes = []
    for i in range(len(hols)):
        holglobes.append( [[0x00,0x00,0x00]] * HolidaySecretAPI.NUM_GLOBES )
        pass

    if maxheight is None:
        if switchback:
            maxheight = float(switchback)
        else:
            maxheight = float(HolidaySecretAPI.NUM_GLOBES)
            pass
        pass

    # Only use the first m values from visdata, based on how many we can display
    m = len(hols) * pieces
    
    for i, value in enumerate(visdata[:m]):
        holid = int(i / pieces)

        # Set the base globe index for each bucket in switchback mode
        if switchback:
            basenum = (i % pieces) * switchback
        else:
            # With no switchback, the bucket basenum is globe 0
            basenum = 0
            pass
        
        # Normalize value based on maxval == maxheight
        if autorange and maxval:
            value = value/maxval * maxheight
            pass

        value = int(value)

        # Clip values greater than maxheight
        if value > maxheight:
            value = int(maxheight)
            pass

        # Set the globes for the holiday for this bucket
        # using switchback if required
        # Use different colours for different height
        # cutoffs, so low values are green, middle yellow/orange
        # and high values are red.
        
        for j in range(0, value):

            # Set the globe index, reversing for switchback mode
            # and using the basenum offset for each switchback bucket 
            if not (i % pieces) % 2:
                globe_idx = basenum + j
            else:
                globe_idx = basenum + (switchback-j) - 1
                pass

            # Set the globe colour based on how far it
            # is from the maximum value
            if (j/maxheight) < 0.4:
                r, g, b = 0, 200, 0
            elif (j/maxheight) < 0.7:
                r, g, b = 222, 215, 26
            else:
                r, g, b = 240, 50, 50
                pass
            holglobes[holid][globe_idx] = [r,g,b]
            pass
        
        # Blank globes above the value in this bucket
        for j in range(value, int(maxheight)):
            if not (i % pieces) % 2:
                globe_idx = basenum + j
            else:
                globe_idx = basenum + (switchback-j) - 1
                pass
            try:
                holglobes[holid][globe_idx] = [0,0,0]
            except IndexError:
                log.error("Failed on holid %d, globe_idx %d", holid, globe_idx)
                raise
        pass

    # Render all the Holidays
    for i, hol in enumerate(hols):
        hol.set_pattern( holglobes[i] )
        hol.render()
        pass
    pass

class HolibeatOptions(optparse.OptionParser):
    """
    Command-line options parser
    """
    def __init__(self, *args, **kwargs):
        optparse.OptionParser.__init__(self, **kwargs)
        self.addOptions()

    def addOptions(self):
        self.add_option('-n', '--numstrings', dest='numstrings',
                        help="Number of Holiday strings to simulate [%default]",
                        type="int", default=1)

        # Listen on multiple TCP/UDP ports, one for each Holiday we simulate
        self.add_option('-p', '--portstart', dest='portstart',
                        help="Port number to start at for UDP listeners [%default]",
                        type="int", default=9988)

        self.add_option('-b', '--buckets', dest='numbuckets',
                        help="Number of frequency bands (buckets) for display",
                        type="int")
        
        self.add_option('-m', '--mode', dest='mode',
                        help="Frequency mode: amplitude or power [%default]",
                        type="choice", choices=['amp', 'power'], default='amp')

        self.add_option('-f', '--fps', dest='fps',
                        help="Frames per second, used to slow down data sending",
                        type="int", default=30)

        self.add_option('', '--switchback', dest='switchback',
                        help="'Switchback' strings, make a single string display like its "
                        "more than one every SWITCHBACK globes",
                        type="int")

        self.add_option('', '--autorange', dest='autorange',
                        help="Dynamically set range of display based on max value",
                        action='store_true', default=True)

        self.add_option('', '--no-autorange', dest='autorange',
                        help="Disable auto-ranging display",
                        action='store_false')
        
        self.add_option('', '--maxheight', dest='maxheight',
                        help="Manually set the maximum height value for buckets",
                        type="float")
        
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

def chunks(l, n):
    """
    Generator for n-sized chunks from list l
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]
        pass

if __name__ == '__main__':
    #list_devices()

    usage = "Usage: %prog [options] <hol_addr:hol_port> [<hol_addr:hol_port> ... ]"
    
    optparse = HolibeatOptions(usage=usage)
    options, args = optparse.parseOptions()
    
    pa = pyaudio.PyAudio()
    
    stream = pa.open(format=FORMAT,
                     channels=CHANNELS,
                     rate=RATE,
                     input=True,
                     frames_per_buffer=BUFSIZE)

    # Sample rate in Hertz
    sample_rate = float(RATE)
    # The Nyquist rate of the signal
    nyq_rate = sample_rate / 2.0

    # A Hamming window, to help with putting frequencies into
    # different buckets.
    window = numpy.hamming(BUFSIZE*2)

    if options.switchback:
        pieces = int(math.floor(float(HolidaySecretAPI.NUM_GLOBES) / options.switchback))
        numbuckets = pieces * options.numstrings
    else:
        pieces = 1
        numbuckets = options.numstrings
        pass

    # Allow manual override of number of buckets
    # Mostly used to clip the higher, less interesting bands, so we visualise the lower
    # bands with more granularity
    if options.numbuckets:
        numbuckets = options.numbuckets
        pass

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
    
    # Build the list of cutoff frequences as powers of 10
    cutoffs = []
    exp = [2, 3, 4]
    for x in exp:
        for i in range(1,10):
            for sub in [0, 1, 2, 3]:
                cutoffs.append( i*(10**x) + sub*(10**x/4) )
                pass
            pass
        pass

    # ignore anything higher than 10kHz because it's boring
    cutoffs = [ x for x in cutoffs if x <= 10000 ]
    #print cutoffs
    
    # chunk cutoffs based on number of strings,
    # and use the max freq val of the chunk for our new cutoff
    cutoffs = [ max(c) for c in chunks(cutoffs, len(cutoffs)/numbuckets) ]

    # Used for auto-ranging of display
    maxval = 0
    maxtime = datetime.datetime.now()

    # Time limiting bits to slow down the UDP firehose
    # This is stupid, but functional. Should be event driven, probably.

    sleeptime = 1.0/options.fps
    while True:
        data = stream.read(BUFSIZE)
        numdata = numpy.fromstring(data, dtype=numpy.short)

        # Normalize data with our sample rate
        normdata = numdata / sample_rate

        # Window the data, using a Hamming window, to better capture
        normdata = normdata * window

        # Use a Fast Fourier Transform to convert to frequency domain
        # Take the absolute value using numpy so the complex number
        # returned by fft() is correctly converted to magnitude information
        # rather than just chopping off the imaginary portion of the complex number
        # discard the second half of the data because it's just aliased from
        # the first half (i.e. repeated because of Nyquist reasons)
        # For more detailed example, see:
        # https://svn.enthought.com/enthought/browser/Chaco/trunk/examples/advanced/spectrum.py
        # See also the doco for Numpy FFT, which explains how to get amplitude and
        # power of the FFT output using different operations
        # http://docs.scipy.org/doc/numpy/reference/routines.fft.html
        fft_data = numpy.fft.fft(normdata)
        freq = numpy.fft.fftfreq(fft_data.size)

        # Ignore the second half of the data
        fft_data = fft_data[:len(fft_data)/2]

        # Convert frequency information into Hz based on the sample_rate
        freq = freq[:len(freq)/2] * sample_rate
        
        # amplitude at each frequency
        fft_amp = numpy.abs(fft_data)

        # power at each frequency
        fft_power = numpy.abs(fft_data)**2

        # Select the values we want to use
        if options.mode == 'amp':
            fft_vals = fft_amp[1:]
        elif options.mode == 'power':
            fft_vals = fft_power[1:]
        else:
            raise ValueError("Invalid mode selected: %s" % options.mode)
        
        # Average data into the number of buckets we want to display
        # We use log-scale for buckets, because most of the interesting
        # information (to humans) is in the lower frequencies.
        visdata = []

        #sys.exit(1)
        vals = []

        cutoff_idx = 0
        for val, f in zip(fft_vals, freq):
            if f < cutoffs[cutoff_idx]:
                vals.append(val)
            else:
                # average values for this bucket and save
                if len(vals) == 0:
                    visdata.append(0)
                else:
                    visdata.append( numpy.average(vals) )
                    pass
                vals = []
                # Update the cutoff value
                cutoff_idx += 1

                # Ignore anything higher than last cutoff
                if cutoff_idx > len(cutoffs)-1:
                    break

                pass
            pass
        
        #print visdata
        #print ["%03d" % x for x in visdata]

        # scale bucket 0 down, because bass always seems to dominate the spectrum
        # particularly for anything not classical music.
        visdata[0] = visdata[0] / 1.8

        for i in range(0, numbuckets):
            # Update auto-ranging information
            if visdata[i] > maxval:
                maxval = visdata[i]
                #log.debug("maxval reset: %f", maxval)
                maxtime = datetime.datetime.now()
                pass
            pass

        # If the maxval was set more than n seconds ago, start
        # reducing the maxval gradually by x% per loop until
        # we have to set the max again
        if datetime.datetime.now() - maxtime > datetime.timedelta(seconds=2):
            #log.debug("maxval %f is old. decreasing...", maxval)
            maxval = maxval - (maxval * 0.05)
            if maxval < 0:
                maxval = 0
            pass
        
        # Send data to Holidays
        send_blinken(hols, visdata, pieces,
                     switchback=options.switchback,
                     maxval=maxval,
                     maxheight=options.maxheight,
                     autorange=options.autorange)
        pass

    # Wait for next timetick
    time.sleep(sleeptime)
    pass
