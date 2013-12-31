#!/usr/bin/env python
"""
UDP interface classes for Holiday

Copyright (c) 2013 Justin Warren <justin@eigenmagic.com>
License: MIT (see LICENSE for details)
"""

__author__ = "Justin Warren"
__version__ = '0.02-dev'
__license__ = "MIT"

import sys
import socket
import array

from base import HolidayBase

import logging

# Set up logging
log = logging.getLogger('udp_holiday')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s: %(name)s [%(levelname)s]: %(message)s"))
log.addHandler(handler)
log.setLevel(logging.DEBUG)

class UDPHoliday(HolidayBase):
    """
    A remote Holiday we talk to over the fast UDP
    """
    def __init__(self, ipaddr, port=9988):
        """
        Initialise the REST Holiday remote address
        @param addr: A string of the remote address of form <ipaddr>:<port>
        """
        super(UDPHoliday, self).__init__()
        self.ipaddr = ipaddr
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def render(self):
        """
        Render globe values via UDP to remote Holiday
        """
        packet = array.array('B', [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # initialize basic packet, ignore first 10 bytes
        for g in self.globes:
            packet.append(g[0])
            packet.append(g[1])
            packet.append(g[2])
            pass
        # Send the packet to the Holiday
        self.sock.sendto(packet, (self.ipaddr, self.port))
        pass
    
