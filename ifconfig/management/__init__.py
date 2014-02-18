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

import os
import socket
import netifaces

from django.core.management import call_command
from django.db.models import signals

import ifconfig.models
import sysutils.models
from ifconfig.models  import Host, NetDevice, IPAddress
from systemd import get_dbus_object, dbus_to_python

def create_interfaces(**kwargs):
    # Make sure we have *this* host in the database
    try:
        host = Host.objects.get_current()
    except Host.DoesNotExist:
        host = Host(name=socket.gethostname())
        host.save()

    vlans = dbus_to_python(get_dbus_object("/ifconfig").get_vconfig())

    ifstack = netifaces.interfaces()
    haveifaces = {}
    have_primary = (IPAddress.objects.filter(primary_address=True).count() > 0)
    unseen_ifaces = [v["devname"] for v in NetDevice.objects.values("devname")]

    while ifstack:
        iface = ifstack.pop(0)
        if iface[:3] == "tap":
            continue

        args = {"host": host, "devname": iface}

        if iface in vlans:
            depends = [vlans[iface][1]]
            iftype  = "VLAN"

        elif os.path.exists( "/sys/class/net/%s/brif" % iface ):
            depends = [depiface for depiface in os.listdir("/sys/class/net/%s/brif" % iface) if "tap" not in depiface]
            iftype  = "BRIDGE"

        elif os.path.exists( "/sys/class/net/%s/bonding/slaves" % iface ):
            depends = open("/sys/class/net/%s/bonding/slaves" % iface).read().strip().split()
            iftype  = "BONDING"
            args["bond_mode"]      =     open("/sys/class/net/%s/bonding/mode"      % iface).read().strip().split()[0]
            args["bond_miimon"]    = int(open("/sys/class/net/%s/bonding/miimon"    % iface).read().strip())
            args["bond_downdelay"] = int(open("/sys/class/net/%s/bonding/updelay"   % iface).read().strip())
            args["bond_updelay"]   = int(open("/sys/class/net/%s/bonding/downdelay" % iface).read().strip())

        else:
            depends = []
            iftype  = "NATIVE"

        havealldeps = True
        for depiface in depends:
            if depiface not in haveifaces:
                havealldeps = False
                break

        if not havealldeps:
            ifstack.append(iface)
            print "Missing dependency for %s" % iface, haveifaces, depends
            continue

        try:
            haveifaces[iface] = NetDevice.objects.get(host=host, devname=iface)
            unseen_ifaces.remove(iface)
            print "Found", iface

        except NetDevice.DoesNotExist:
            print "Adding", iface
            haveifaces[iface] = NetDevice(**args)
            haveifaces[iface].save()
            unseen_ifaces.remove(iface)

            if iftype in ("BRIDGE", "BONDING"):
                depifaces = [ haveifaces[depiface] for depiface in depends ]
                if iftype == "BRIDGE":
                    haveifaces[iface].brports = depifaces
                else:
                    haveifaces[iface].slaves  = depifaces

            elif iftype == "VLAN":
                haveifaces[iface].vlanrawdev  = NetDevice.objects.get(devname=depends[0])

        #print "%s is a %s device with depends to %s" % ( iface, iftype, ','.join(depends) )
        #print args

        for addrfam, addresses in netifaces.ifaddresses(iface).iteritems():
            if addrfam not in ( socket.AF_INET, socket.AF_INET6 ):
                continue
            for addr in addresses:
                if addrfam == socket.AF_INET6 and addr["addr"][:4] == "fe80":
                    # Don't record link-local addresses
                    continue
                is_primary = not have_primary and addr["addr"] not in ("127.0.0.1", "::1")
                have_primary = have_primary or is_primary
                try:
                    ip = IPAddress.objects.get( device__host=host, address__startswith=addr["addr"]+"/" )
                except IPAddress.DoesNotExist:
                    print "Adding ", addr
                    ip = IPAddress(address=(addr["addr"] + "/" + addr["netmask"]), device=haveifaces[iface], primary_address=is_primary)
                    ip.save()

    for iface in unseen_ifaces:
        print "Removing unseen interface", iface
        NetDevice.objects.get(devname=iface).delete()

sysutils.models.post_install.connect(create_interfaces, sender=sysutils.models)
