# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

"""
 *  Copyright (C) 2011-2012, it-novum GmbH <community@open-attic.org>
 *
 *  openATTIC is free software; you can redistribute it and/or modify it
 *  under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; version 2.
 *
 *  This package is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
"""

from threading import Lock
from os.path import getmtime, exists
from time import sleep

class NagiosState(object):
    """ Dict-like class to access Nagios's status information.

        The data returned by this object is always up-to-date, because all getters
        check if the file has been updated in the meantime before returning data.
    """
    def __init__(self, statfile="/var/cache/nagios3/status.dat"):
        self.statfile    = statfile
        self.timestamp   = 0
        self.nagstate    = None
        self._servicemap = {}
        self.lock        = Lock()

    def __getitem__(self, name):
        self.update()
        return self.nagstate[name]

    def __len__(self):
        self.update()
        return len(self.nagstate)

    def __iter__(self):
        self.update()
        return iter(self.nagstate)

    def keys(self):
        self.update()
        return self.nagstate.keys()

    def values(self):
        self.update()
        return self.nagstate.values()

    @property
    def servicemap(self):
        self.update()
        return self._servicemap

    def update(self):
        try:
            self.lock.acquire()
            if exists(self.statfile):
                mtime = getmtime(self.statfile)
            else:
                raise SystemError("'%s' does not exist" % self.statfile)

            if mtime > self.timestamp:
                self.nagstate  = self.parse_status()
                self.timestamp = mtime
        finally:
            self.lock.release()

    def parse_status(self):
        ST_BEGINSECT, ST_SECTNAME, ST_BEGINVALUE, ST_VALUE, ST_COMMENT = range(5)
        state = ST_BEGINSECT

        result = {}
        self._servicemap = {}

        currsect  = ''
        currname  = ''
        currvalue = ''
        curresult = {}

        with open( self.statfile, "rb" ) as nag:
            while True:
                buf = nag.read(4096)
                if not buf:
                    break

                for char in buf:
                    if state == ST_BEGINSECT:
                        if char == '{':
                            raise ValueError("{ but no section name?")
                        elif char in (' ', '\t', '\r', '\n'):
                            pass
                        elif char == '#':
                            state = ST_COMMENT
                        else:
                            currsect += char
                            state = ST_SECTNAME

                    elif state == ST_SECTNAME:
                        if char == '{':
                            state = ST_BEGINVALUE
                            if currsect not in result:
                                result[currsect] = []
                        elif char == ' ':
                            pass
                        else:
                            currsect += char

                    elif state == ST_BEGINVALUE:
                        if char in (' ', '\t', '\r', '\n'):
                            pass
                        elif char == '=':
                            state = ST_VALUE
                        elif char == '}':
                            state = ST_BEGINSECT
                            result[currsect].append(curresult)
                            if currsect == "servicestatus":
                                self._servicemap[curresult["service_description"]] = curresult
                            curresult = {}
                            currsect = ''
                        else:
                            currname += char

                    elif state == ST_VALUE:
                        if char == '\r':
                            pass
                        elif char == '\n':
                            state = ST_BEGINVALUE
                            curresult[currname] = currvalue
                            currname  = ''
                            currvalue = ''
                        else:
                            currvalue += char

                    elif state == ST_COMMENT:
                        if char == '\n':
                            state = ST_BEGINSECT

        return result
