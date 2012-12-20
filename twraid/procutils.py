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

import errno
import re

from systemd.procutils import invoke

from twraid import models

class TwRegex:
    ctl         = (r'^(?P<ctl>c\d+)\s+(?P<model>[\w\-]+)\s+(?P<ports>\d+)\s+(?P<drives>\d+)\s+(?P<units>\d+)\s+'
                     '(?P<notopt>\d+)\s+(?P<rrate>\d+)\s+(?P<vrate>\d+)\s+(?P<bbu>\w+|-)$')

    enclosure   = (r'^(?P<encl>/c\d+/e\d+)\s+(?P<slots>\d+)\s+(?P<drives>\d+)\s+(?P<fans>\d+)\s+'
                     '(?P<tsunits>\d+)\s+(?P<psunits>\d+)\s+(?P<alarms>\d+)$')

    ctlparam    = (r'^/(?P<ctl>c\d+)\s(?P<key>[^=]+)=(?P<value>.*)$')

    ctlunit     = (r'^(?P<unit>u\d+)\s+(?P<unittype>[\w\-]+)\s+(?P<status>[\w\-]+)\s+(?P<rcmpl>[\w\-]+)\s+'
                     '(?P<vim>[\w\-]+)\s+(?P<chunksize>[\w\-]+)\s+(?P<totalsize>[\w\.\-]+)\s+(?P<cache>[\w\-]+)\s+(?P<avrfy>[\w\-]+)$')

    ctlport     = (r'^(?P<port>p\d+)\s+(?P<status>[\w\-]+)\s+(?P<unit>(u\d+|-)+)\s+(?P<size>[\w\.\-]+ \w+B)\s+(?P<type>[\w\-]+)\s+'
                     '(?P<phy>[\w\-]+)\s+(?P<slot>/c\d+/e\d+/slt\d+)\s+(?P<model>[\w\s\-]+)$')

    unitparam   = (r'^/(?P<unit>c\d+/u\d+)\s(?P<key>[^=]+)=(?P<value>.*)$')

    unitdisk    = (r'^(?P<unit>u\d+-\d+)\s+DISK\s+(?P<status>[\w\-]+)\s+(?P<rcmpl>[\w\-]+)\s+(?P<vim>[\w\-]+)\s+'
                     '(?P<port>p\d+|-)\s+-\s+\s+(?P<size>[\w\.\-]+)$')

    diskparam   = (r'^/(?P<port>c\d+/p\d+)\s(?P<key>[^=]+)=(?P<value>.*)$')



class Bunch(object):
    def __init__(self, data):
        self.__dict__.update(data)

class Controller(Bunch):
    def __init__(self, data):
        Bunch.__init__(self, data)
        self.enclosures = {}
        self.params = {}
        self.units  = {}
        self.ports  = {}

    @property
    def id(self):
        return int(self.ctl[1:])

class Enclosure(Bunch):
    @property
    def ctl_id(self):
        return int(re.match("/c(\d+)/e\d+", self.encl).group(1))

    @property
    def id(self):
        return int(re.match("/c\d+/e(\d+)", self.encl).group(1))

class Unit(Bunch):
    def __init__(self, data):
        Bunch.__init__(self, data)
        self.params = {}
        self.disks  = {}

    @property
    def id(self):
        return int(self.unit[1:])

class Disk(Bunch):
    def __init__(self, data):
        Bunch.__init__(self, data)
        self.params = {}

    @property
    def id(self):
        return int(self.unit.split('-')[1])

    @property
    def port_id(self):
        return int(self.port[1:])

    @property
    def unit_id(self):
        if not hasattr(self, "unit"):
            return None
        return int(self.unit.split('-')[0][1:])

    @property
    def unit_disk(self):
        if not hasattr(self, "unit"):
            return None
        return int(self.unit.split('-')[1])

    @property
    def ctl_id(self):
        return int(re.match("/c(\d+)/e\d+/slt\d+", self.slot).group(1))

    @property
    def encl_id(self):
        return int(re.match("/c\d+/e(\d+)/slt\d+", self.slot).group(1))

    @property
    def slot_id(self):
        return int(re.match("/c\d+/e\d+/slt(\d+)", self.slot).group(1))



def query_ctls():
    ctls = {}

    twcli = "tw-cli"
    try:
        ret, out, err = invoke([twcli, "show"], return_out_err=True, log=False)
    except OSError, err:
        print "tw-cli not found"
        if err.errno != errno.ENOENT:
            raise
        # tw-cli was not found. retry using tw_cli, which may or may not work.
        # if it does, use tw_cli from now on.
        twcli = "tw_cli"
        try:
            ret, out, err = invoke([twcli, "show"], return_out_err=True, log=False)
        except OSError, err:
            if err.errno != errno.ENOENT:
                raise
            raise SystemError("tw-cli not installed")

    for line in out.split("\n"):
        line = line.strip()
        if not line:
            continue

        m = re.match(TwRegex.ctl, line)
        if m:
            print "Found controller!", m.groupdict()
            ctl = Controller(m.groupdict())
            ctls[ctl.id] = ctl
            continue

        m = re.match(TwRegex.enclosure, line)
        if m:
            print "Found enclosure!", m.groupdict()
            encl = Enclosure(m.groupdict())
            ctls[encl.ctl_id].enclosures[encl.id] = encl
            continue

    if not ctls:
        return ctls

    for ctl_id, ctl in ctls.items():
        ret, out, err = invoke([twcli, "/" + ctl.ctl, "show", "all"], return_out_err=True, log=False)
        for line in out.split("\n"):
            line = line.strip()
            if not line:
                continue

            m = re.match(TwRegex.ctlparam, line)
            if m:
                print "Found controller property!", m.groupdict()
                ctl.params[ m.group("key").strip().lower() ] = m.group("value").strip()
                continue

            m = re.match(TwRegex.ctlunit, line)
            if m:
                print "Found Unit!", m.groupdict()
                have_units = True
                unit = Unit(m.groupdict())
                ctl.units[unit.id] = unit
                continue

            m = re.match(TwRegex.ctlport, line)
            if m:
                print "Found Disk (Port)!", m.groupdict()
                disk = Disk(m.groupdict())
                ctl.ports[disk.port_id] = disk
                continue

        for port_id, disk in ctl.ports.items():
            ret, out, err = invoke([twcli, "/c%d/p%d" % (disk.ctl_id, disk.port_id), "show", "all"], return_out_err=True, log=False)
            for line in out.split("\n"):
                line = line.strip()
                if not line:
                    continue

                m = re.match(TwRegex.diskparam, line)
                if m:
                    print "Found disk property!", m.groupdict()
                    disk.params[ m.group("key").strip().lower() ] = m.group("value").strip()
                    continue

        if not ctl.units:
            continue

        for unit_id, unit in ctl.units.items():
            ret, out, err = invoke([twcli, "/%s/%s" % (ctl.ctl, unit.unit), "show", "all"], return_out_err=True, log=False)
            for line in out.split("\n"):
                line = line.strip()
                if not line:
                    continue

                m = re.match(TwRegex.unitparam, line)
                if m:
                    print "Found unit property!", m.groupdict()
                    unit.params[ m.group("key").strip().lower() ] = m.group("value").strip()
                    continue

                m = re.match(TwRegex.unitdisk, line)
                if m:
                    print "Found Disk (unit)!", m.groupdict()
                    disk = ctl.ports[ int(m.group("port")[1:]) ]
                    disk.__dict__.update(m.groupdict())
                    unit.disks[disk.id] = disk
                    continue

    return ctls


def update_database(ctls):
    host = models.Host.objects.get_current()

    for ctl_id, ctl in ctls.items():
        try:
            dbctl = models.Controller.objects.get(host=host, serial=ctl.params["serial number"])
        except models.Controller.DoesNotExist:
            dbctl = models.Controller(host=host, serial=ctl.params["serial number"])

        if ctl.bbu != '-':
            dbctl.bbustate = ctl.bbu
        else:
            dbctl.bbustate = ''

        dbctl.index     = ctl_id
        dbctl.model     = ctl.params["model"]
        dbctl.actdrives = int(ctl.params["active drives"].split(" of ")[0])
        dbctl.curdrives = int(ctl.params["drives"].split(" of ")[0])
        dbctl.maxdrives = int(ctl.params["active drives"].split(" of ")[1])
        dbctl.actunits  = int(ctl.params["active units"].split(" of ")[0])
        dbctl.curunits  = int(ctl.params["units"].split(" of ")[0])
        dbctl.maxunits  = int(ctl.params["active units"].split(" of ")[1])
        dbctl.autorebuild = (ctl.params["auto-rebuild policy"].lower() == 'on')
        dbctl.save()

        for encl_id, encl in ctl.enclosures.items():
            try:
                dbencl = models.Enclosure.objects.get(controller=dbctl, index=encl_id)
            except models.Enclosure.DoesNotExist:
                dbencl = models.Enclosure(controller=dbctl, index=encl_id)

            dbencl.alarms  = encl.alarms
            dbencl.slots   = encl.slots
            dbencl.fans    = encl.fans
            dbencl.tsunits = encl.tsunits
            dbencl.psunits = encl.psunits
            dbencl.save()

        for unit_id, unit in ctl.units.items():
            try:
                dbunit = models.Unit.objects.get(controller=dbctl, serial=unit.params["serial number"])
            except models.Unit.DoesNotExist:
                dbunit = models.Unit(controller=dbctl, serial=unit.params["serial number"])

            dbunit.index      = unit_id
            dbunit.unittype   = unit.unittype
            dbunit.status     = unit.status
            dbunit.rebuild    = unit.rcmpl if unit.rcmpl != '-' else None
            dbunit.verify     = unit.vim if unit.vim != '-' else None
            dbunit.chunksize  = int(unit.chunksize[:-1]) * 1024 if unit.chunksize != '-' else None
            dbunit.size       = int(float(unit.totalsize) * 1024)
            dbunit.autoverify = (unit.avrfy.lower() == 'on')

            dbunit.rdcache    = unit.params["read cache"]
            dbunit.wrcache    = unit.params["write cache"]
            dbunit.name       = unit.params["name"]
            dbunit.save()

        for port_id, disk in ctl.ports.items():
            try:
                dbdisk = models.Disk.objects.get(controller=dbctl, serial=disk.params["serial"])
            except models.Disk.DoesNotExist:
                dbdisk = models.Disk(controller=dbctl, serial=disk.params["serial"])

            dbdisk.port       = port_id
            dbdisk.disktype   = disk.type
            dbdisk.encl       = models.Enclosure.objects.get(controller=dbctl, index=disk.encl_id)
            dbdisk.enclslot   = disk.slot_id
            dbdisk.size       = int(float(disk.size[:-3]) * 1024)
            dbdisk.model      = disk.model
            if disk.unit != '-':
                dbdisk.unit   = models.Unit.objects.get(controller=dbctl, index=disk.unit_id)
                dbdisk.unitindex = disk.unit_disk
            else:
                dbdisk.unit   = None
                dbdisk.unitindex = None
            dbdisk.rpm        = int( re.match("^(\d+)", disk.params["spindle speed"]).group(1) )
            dbdisk.status     = disk.params["status"]
            dbdisk.temp_c     = int( re.match("^(\d+)", disk.params["temperature"]).group(1) )
            dbdisk.linkspeed  = float( re.match("^(\d+\.\d+)", disk.params["link speed"]).group(1) )
            dbdisk.power_on_h = int( disk.params["power on hours"] )

            dbdisk.save()
