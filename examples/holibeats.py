#!/usr/bin/python
#
# A SoundLevel monitor on a Holiday for sound playing on your PC
#
import sys
import pyaudio
import audioop
import numpy
import scipy
import time
#from scipy.signal import kaiserord, lfilter, firwin, freqz

from scipy import fft

import optparse

from secretapi.holidaysecretapi import HolidaySecretAPI

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
BUFSIZE = 2048

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

def send_blinken(hol, value, maxval=None):
    """
    Create a light pattern for a remote Holiday
    based on the value we receive.

    If maxval is supplied, scale value as proportion of
    maxval, so the display auto-ranges.
    """
    # Normalize value based on maxval == 48 globes
    if maxval:
        value = value/maxval * 48
        pass
    
    value = int(value)

    # Clip values greater than 50
    if value > 50:
        value = 50
        pass

    for i in range(0, value):
        if i < 25:
            hol.setglobe(i, 50, 180, 50)
        elif i < 40:
            hol.setglobe(i, 222, 215, 26)
        else:
            hol.setglobe(i, 200, 50, 50)
        pass
    
    for i in range(value, 51):
        hol.setglobe(i, 0, 0, 0)
        pass

    hol.render()

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

        self.add_option('-m', '--mode', dest='mode',
                        help="Frequency mode: amplitude or power [%default]",
                        type="choice", choices=['amp', 'power'], default='amp')

        self.add_option('-f', '--fps', dest='fps',
                        help="Frames per second, used to slow down data sending",
                        type="int", default=30)
        
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

def chunks(l, n):
    """
    Generator for n-sized chunks from list l
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]
        pass

if __name__ == '__main__':
    #list_devices()
    optparse = HolibeatOptions()
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

    hols = []
    for i in range(0, options.numstrings):
        hols.append(HolidaySecretAPI(port=options.portstart+i))
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
    cutoffs = [ max(c) for c in chunks(cutoffs, len(cutoffs)/options.numstrings) ]
    #print cutoffs

    # Used for auto-ranging of display
    maxval = 0

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
        visdata[0] = visdata[0] / 1.5

        for i in range(0, options.numstrings):
            # Update auto-ranging information
            if visdata[i] > maxval:
                maxval = visdata[i]
                pass
            send_blinken(hols[i], visdata[i], maxval)
            pass
        pass

    # Wait for next timetick
    time.sleep(sleeptime)
    pass
