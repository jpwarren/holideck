#!/usr/bin/env python
"""
REST interface classes for Holiday

Copyright (c) 2013 Justin Warren <justin@eigenmagic.com>
License: MIT (see LICENSE for details)
"""

__author__ = "Justin Warren"
__version__ = '0.02-dev'
__license__ = "MIT"

import requests
import json

from base import HolidayBase

import logging

# Set up logging
log = logging.getLogger('rest_holiday')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s: %(name)s [%(levelname)s]: %(message)s"))
log.addHandler(handler)
log.setLevel(logging.DEBUG)

class RESTHoliday(HolidayBase):
    """
    A remote Holiday we talk to over the JSON REST web interface
    """
    def __init__(self, addr, scheme='http'):
        """
        Initialise the REST Holiday remote address
        @param addr: A string of the remote address of form <ipaddr>:<port>
        """
        super(RESTHoliday, self).__init__()
        self.scheme = scheme
        self.addr = addr
        
    def render(self):
        """
        Render globe values via JSON to remote Holiday via REST interface
        """
        hol_vals = [ "#%02x%02x%02x" % (x[0], x[1], x[2]) for x in self.globes ]
        hol_msg = { "lights": hol_vals }
        msg_str = json.dumps(hol_msg)
        url_str = "%s://%s/device/light/setlights" % (self.scheme, self.addr)
        r = requests.put(urlstr, data=msg_str)
        pass
    
