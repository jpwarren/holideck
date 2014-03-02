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
                 autorange=True,
                 colorscheme='default'):
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
            (r, g, b) = get_val_color( j/maxheight, colorscheme )
            #log.debug("%d %d %d %d", globe_idx, r, g, b)
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

def get_val_color(val, scheme='default'):
    """
    Return the globe color based on the scheme we're using.

    @param val: is a float value between 0.0 and 1.0
    """
    if scheme == 'default':
        if val < 0.3:
            r, g, b = 0, 200, 0 # green
        elif val < 0.7:
            r, g, b = 220, 220, 00 # yellow
        else:
            r, g, b = 240, 10, 10 # red
        pass

    elif scheme == 'blue':
        r, g, b = 0, 0, 30 + 225 * val
    elif scheme == 'red':
        r, g, b = 30 + 225 * val, 0, 0
    elif scheme == 'green':
        r, g, b = 0, 30 + 225 * val, 0

    elif scheme == 'yellow':
        r, g, b = 30 + 225 * val, 30 + 225 * val, 0
        pass

    elif scheme == 'oz':
        if val < 0.4:
            r, g, b = 0, 30 + 225 * val, 0
        else:
            r, g, b = 30 + 225 * val, 30 + 225 * val, 0
            pass
        pass
    
    r = int(r)
    g = int(g)
    b = int(b)
    return (r, g, b)

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

        self.add_option('-c', '--colorscheme', dest='colorscheme',
                        help=" [%default]",
                        type="choice", choices = ['default', 'blue', 'green', 'red', 'yellow', 'oz'],
                        default='default')
        
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
                        help="Dynamically set range of display based on max value [%default]",
                        action='store_true', default=True)

        self.add_option('', '--no-autorange', dest='autorange',
                        help="Disable auto-ranging display",
                        action='store_false')
        
        self.add_option('', '--maxheight', dest='maxheight',
                        help="Manually set the maximum height value for buckets",
                        type="float")
        
        self.add_option('', '--avgvals', dest='num_maxvals',
                        help="Number of samples to calculate moving average for maxval over.",
                        type="int", default=50)
        
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
    # different buckets. Use twice as many as strings, because everything high is boring.
    window = numpy.hamming(BUFSIZE*2)

    if options.switchback:
        pieces = int(math.floor(float(HolidaySecretAPI.NUM_GLOBES) / options.switchback))
        numbuckets = pieces * options.numstrings * 2
    else:
        pieces = 1
        numbuckets = options.numstrings * 2
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
    
    # Build the list of cutoff frequences as powers of 2
    cutoffs = []
    base = 20
    
    maxfreq = 20000 # anything higher than this is super boring
    steps = int(math.log(maxfreq, base))
    exp = range(1, steps, 1)

    sublist = range(0, base)
    
    for x in exp:
        for i in range(1, base, 1):
            for sub in sublist:
                cutoffs.append( i*(base**x) + sub*(base**x/len(sublist)) )
                pass
            pass
        pass

    # ignore anything higher than 10kHz because it's boring
    cutoffs = [ x for x in cutoffs if x <= maxfreq ]
    #print cutoffs

    # chunk cutoffs based on number of strings,
    # and use the max freq val of the chunk for our new cutoff
    cutoffs = [ max(c) for c in chunks(cutoffs, len(cutoffs)/numbuckets) ]
    #print cutoffs
    #sys.exit(1)
    
    # Used for auto-ranging of display
    maxvals = []
    current_maxval = 0

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

        bucket_maxval = 0
        for i in range(0, numbuckets):
            # Update auto-ranging information
            if visdata[i] > bucket_maxval:
                bucket_maxval = visdata[i]
                pass
            pass

        # new maxval is the average of the last n maxvals
        maxvals.insert(0, bucket_maxval)
        maxvals = maxvals[:options.num_maxvals]

        current_maxval = numpy.average(maxvals)
        #log.debug("maxval reset: %f", maxval)

        #print "current max:", current_maxval
        
        # Send data to Holidays
        send_blinken(hols, visdata, pieces,
                     switchback=options.switchback,
                     maxval=current_maxval,
                     maxheight=options.maxheight,
                     autorange=options.autorange,
                     colorscheme=options.colorscheme)
        pass

    # Wait for next timetick
    time.sleep(sleeptime)
    pass
