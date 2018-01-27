#!/usr/bin/env python

# MIT License
# 
# Copyright (c) 2018 Dan Persons (dpersonsdev@gmail.com)
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from time import sleep
from datetime import datetime
import socket
import re
import os.path
import json

from django.utils import timezone
import ldsiparser.parsers
from siem.models import LogEvent
from ldsi.settings import TIME_ZONE

class LiveParser:

    #def __init__(self, db, helpers):
    def __init__(self):
        """Initialize live parser"""

        self.parser = None
        #self.helpers = helpers


    def get_parsers(self):
        """Load parser modules"""
        for parser in sorted(ldsiparser.parsers.__all__):
            self.parsers[parser] = \
                    __import__('ldsiparser.parsers.' + parser, globals(),
                            locals(), [ldsiparser]).ParseModule()
    
    def parse_entries(self, inputfile, parser):
        """Parse log entries from a file like object"""

        # Get hostname, file name, tzone:
        parsepath = os.path.abspath(inputfile.name)
        parsehost = socket.getfqdn()
        timezone.activate(TIME_ZONE)

        # Read to the end of the file:
        inputfile.read()
        
        #rehelpers = []
        #for h in helpers:
        #    reh = {}
        #    reh['var_name'] = h['var_name']
        #    reh['reg_exp'] = re.compile(h['reg_exp'])
        #    rehelpers.append(reh)

        while True:

            # Check for a new line:
            line = inputfile.readline()

            if line:
                # Do the parsing
                ourline = line.rstrip()
                
                entry = self.parser.parse_line(ourline)

                if entry:
                    
                    # Parse extended attributes from helpers:
                    #extattrs = {}
                    #
                    #for h in rehelpers:
                    #    mlist = h['reg_exp'].findall(entry['message'])
                    #
                    #    try:
                    #        extattrs[h['var_name']] += mlist
                    #    except KeyError:
                    #        extattrs[h['var_name']] = mlist
                    #
                    #extattrs = json.dumps(extattrs)

                    e = LogEvent()
                    e.parsed_at = timezone.localtime(timezone.now())
                    e.time_zone = TIME_ZONE
                    e.date_stamp = entry['date_stamp']
                    e.raw_text = ourline
                    e.facility = entry['facility']
                    e.severity = entry['severity']
                    e.source_host = entry['source_host']
                    e.source_port = entry['source_port']
                    e.dest_host = entry['dest_host']
                    e.dest_port = entry['dest_port']
                    e.source_process = entry['source_process']
                    e.source_pid = entry['source_pid']
                    e.protocol = entry['protocol']
                    e.message = entry['message']
                    e.parsed_on = parsehost
                    e.source_path = parsepath
                    e.save()

                else:
                    # No match
                    e = LogEvent()
                    e.parsed_at = timezone.localtime(timezone.now())
                    e.time_zone = TIME_ZONE
                    e.raw_text = ourline
                    e.parsed_on = parsehost
                    e.source_path = parsepath

            else:
                sleep(0.1)


    def parse_file(self, filename, parser):
        try:
            with open(filename, 'r') as inputfile:
                p = self.get_parser(parser)
                self.parse_entries(inputfile, p)

        except KeyboardInterrupt:
            pass
        # except Exception as err:
        #     print('Error: ' + str(err))


def start_parse(db, parseinfo):
    #parser = LiveParser(db, parseinfo['helpers'])
    parser = LiveParser()
    parser.parse_file(parseinfo['filename'], parseinfo['parser'])