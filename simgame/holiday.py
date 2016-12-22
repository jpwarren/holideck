"""
Simulated Holiday Server
"""
import select, socket, os
import array

from Queue import Empty
from multiprocessing import Process, Queue
from iotas import iotas

UDP_HEADER_LENGTH = 10
UDP_DATA_LENGTH = 150
UDP_MSG_LENGTH = UDP_HEADER_LENGTH + UDP_DATA_LENGTH

class HolidayRemote(object):
    """
    A simulated remote Holiday.

    This object pretends to be a physical Holiday light, which
    listens for instructions via both TCP (for the WebAPI) and
    also via UDP (using the SecretLabsAPI).
    """
    # FIXME: The core code should all be in one place, not duplicated
    # in every subdirectory the way it is now.
    NUM_GLOBES = 50
    def __init__(self, remote=False, addr='',
                 tcpport=None,
                 udpport=None,
                 notcp=False,
                 noudp=False,
                 nofifo=False,
    ):

        # Initialise globes to zero
        self.globes = [ [0x00, 0x00, 0x00] ] * self.NUM_GLOBES

        self.notcp = notcp
        self.noudp = noudp
        self.nofifo = nofifo
        
        if not remote:
            self.addr = addr

            if not noudp:
                if udpport is None:
                    bound_port = False
                    for udpport in range(9988, 10100):
                        try:
                            self.bind_udp(udpport)
                            bound_port = True
                            break
                        except socket.error, e:
                            num, s = e
                            # Try again if port is in use, else raise
                            if num != 98:
                                raise
                            pass
                        pass
                    # If we get this far, bail out
                    if not bound_port:
                        raise ValueError("Can't find available UDP port in range 9988 to 10100")

                else:
                    self.bind_udp(udpport)
                    pass
                print "UDP listening on (%s, %s)" % (self.addr, self.udpport)
                pass
            
            # Set up REST API on a TCP port
            if not notcp:    
                self.q = Queue()

                self.iop = Process(target=iotas.run, kwargs={ 'port': 8080,
                                                          'queue': self.q })
                self.iop.start()

            # Set up a named pipe for local single string simulation
            if not nofifo:
                fd = os.open('/run/compose.fifo', os.O_RDONLY | os.O_NONBLOCK)
                self.fifofp = os.fdopen(fd, 'r')
                self.fifobuf = ''
                self.fifobytes = (18) + (9 * self.NUM_GLOBES)
        else:
            raise NotImplementedError("Listening Simulator only. Does not send to remote devices.")

    def exit(self):
        """
        Force shutdown of processes
        """
        if hasattr(self, 'iop'):
            self.iop.terminate()

    def __del__(self):
        self.exit()
        
    def bind_udp(self, udpport):
        """
        Try to bind to a UDP port, retrying a range if one is already in use
        """
        self.udpport = udpport
        self.udpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpsock.setblocking(0)
        self.udpsock.bind((self.addr, self.udpport))
        
    def recv_udp(self):
        """
        Receive data on the UDP port and process it
        """
        try:
            data, addr = self.udpsock.recvfrom(512) # 512 byte buffer. Should be heaps
        except socket.error, e:
            num, msg = e
            # This is EWOULDBLOCK, which we ignore
            if num == 11:
                return

        # Basic check that data is in the right format
        # All SecretLabsAPI packets should be 160 bytes:
        # 10 bytes of header (unused atm) and 150 bytes of data
        if len(data) != UDP_MSG_LENGTH:
            # Just ignore it for now
            print "Incorrect msg length: %d" % len(data)
            return

        header = data[:10]
        globedata = array.array('B', data[10:])

        # Iterate over globedata 3 at a time
        # FIXME: replace with something from itertools?
        for i in range(0, self.NUM_GLOBES):
            coldata = globedata[:3]
            globedata = globedata[3:]
            self.globes[i] = [ coldata[0], coldata[1], coldata[2] ]
            pass
        
    def recv_tcp(self):
        """
        Receive data on the TCP port and process it

        Reception of data is via the Queue
        """
        # Get all the data available, and only use the latest
        # This will throw away all old data if the main loop is
        # too slow, so we at least catch up.
        data = None
        while True:
            try:
                data = self.q.get(block=False)

            except Empty:
                break
            pass

        if data is not None:
            # Data is a list of globe values encoded as
            # 3 x 2-char hex values, one per line
            globedata = data.split()
            for i, vals in enumerate(globedata):
                r = int(vals[:2], 16)
                g = int(vals[2:4], 16)
                b = int(vals[4:6], 16)
                self.globes[i] = [ r, g, b ]
                pass
            pass
        pass

    def recv_fifo(self):
        """
        Try to read data from the FIFO.
        Data starts with a header of 0x000010 followed by the hex encoded
        PID value of the sending process.
        Each globe value is encoded as 3 x 2-char hex values,
        with a 0x prefix.
        It is a total of 468 bytes long for a 50 globe string.
        """
        try:
            self.fifobuf += self.fifofp.read(self.fifobytes)
        except IOError, e:
            # Error 11 is when data isn't available on the pipe
            # so we ignore it.
            if e.errno == 11:
                pass

        # Only process when there is enough data
        while len(self.fifobuf) >= self.fifobytes:
            data = self.fifobuf[:self.fifobytes]
            self.fifobuf = self.fifobuf[self.fifobytes:]
            header = data[:9]
            pid = data[9:18]
            globeraw = data[18:]
            globedata = globeraw.split('\n')
            
            for i, vals in enumerate(globedata[:self.NUM_GLOBES]):
                if len(vals) < 8:
                    break
                r = int(vals[2:4], 16)
                g = int(vals[4:6], 16)
                b = int(vals[6:8], 16)
                self.globes[i] = [ r, g, b ]
