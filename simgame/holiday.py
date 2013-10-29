"""
Simulated Holiday Server
"""
import select, socket
import array

UDP_HEADER_LENGTH = 10
UDP_DATA_LENGTH = 150
UDP_MSG_LENGTH = UDP_HEADER_LENGTH + UDP_DATA_LENGTH

class HolidayRemote(object):
    """
    A simulated remote Holiday.

    This object pretends to be a physical Holiday light, which
    listens for instructions via both TCP (for the WebAPI) and
    also via UDP (using the SecretLabsAPI).

    FIXME: Only the UDP interface is implemented for now.
    """
    # FIXME: The core code should all be in one place, not duplicated
    # in every subdirectory the way it is now.
    NUM_GLOBES = 50
    def __init__(self, remote=False, addr='',
                 tcpport=None,
                 udpport=None):

        # Initialise globes to zero
        self.globes = [ [0x00, 0x00, 0x00] ] * self.NUM_GLOBES

        if not remote:
            self.addr = addr
            self.tcpport = tcpport
            if udpport is None:
                bound_port = False
                for port in range(9988, 10100):
                    try:
                        self.bind_udp(port)
                        bound_port = True
                        break
                    except socket.error, e:
                        num, s = e
                        # Ignore Address already in use
                        if num != 98:
                            raise
                        pass
                    pass
                # If we get this far, bail out
                if not bound_port:
                    raise ValueError("Can't find available UDP port in range 9988 to 10100")
            
            else:
                self.bind_udp(udpport)
            print "UDP listening on (%s, %s)" % (self.addr, self.udpport)
        else:
            raise NotImplementedError("Listening Simulator only. Does not send to remote devices.")

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
        
