# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

"""
 *  Copyright (C) 2011-2014, it-novum GmbH <community@open-attic.org>
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

import re
import os
import os.path
import json
import sysutils.models

from ConfigParser import ConfigParser

from django.contrib.auth.models import User

from systemd import get_dbus_object, dbus_to_python
from ifconfig.models import Host, IPAddress
from ceph import models as ceph_models
from volumes.models import StorageObject


def update(**kwargs):
    admin = User.objects.filter( is_superuser=True )[0]

    if not os.path.exists("/etc/ceph"):
        print "Ceph does not appear to be installed, skipping detection"
        return

    for fname in os.listdir("/etc/ceph"):
        m = re.match(r'^(?P<displayname>\w+)\.conf$', fname)
        if m is None:
            continue

        displayname = m.group("displayname")

        conf = ConfigParser()
        if not conf.read("/etc/ceph/%s.conf" % displayname):
            print "%s.conf doesn't seem to be a valid config file, skipping" % displayname
            continue

        print "Checking Ceph cluster %s (%s)..." % (displayname, conf.get("global", "fsid")),
        try:
            cluster = ceph_models.Cluster.objects.get(uuid=conf.get("global", "fsid"))
            print "known"
        except ceph_models.Cluster.DoesNotExist:
            cluster = ceph_models.Cluster(uuid=conf.get("global", "fsid"), displayname=displayname,
                                        auth_cluster_required = conf.get("global", "auth_cluster_required"),
                                        auth_service_required = conf.get("global", "auth_service_required"),
                                        auth_client_required  = conf.get("global", "auth_client_required"),
                                        )
            cluster.full_clean()
            cluster.save()
            print "added"

        osdmap   = json.loads(dbus_to_python(get_dbus_object("/ceph").osd_dump(cluster.displayname)))
        crushmap = json.loads(dbus_to_python(get_dbus_object("/ceph").osd_crush_dump(cluster.displayname)))
        mds_stat = json.loads(dbus_to_python(get_dbus_object("/ceph").mds_stat(cluster.displayname)))
        mon_stat = json.loads(dbus_to_python(get_dbus_object("/ceph").mon_status(cluster.displayname)))
        auth_list= json.loads(dbus_to_python(get_dbus_object("/ceph").auth_list(cluster.displayname)))
        df       = json.loads(dbus_to_python(get_dbus_object("/ceph").df(cluster.displayname)))

        for ctype in crushmap["types"]:
            print "Checking ceph type '%s'..." % ctype["name"],
            try:
                mdltype = ceph_models.Type.objects.get(cluster=cluster, ceph_id=ctype["type_id"])
                print "known"
            except ceph_models.Type.DoesNotExist:
                mdltype = ceph_models.Type(cluster=cluster, ceph_id=ctype["type_id"], name=ctype["name"])
                mdltype.full_clean()
                mdltype.save()
                print "added"

        buckets = crushmap["buckets"][:]
        osdbuckets = {}
        while buckets:
            cbucket = buckets.pop(0)

            # First make sure the bucket is known to the DB.
            print "Checking ceph bucket '%s %s'..." % (cbucket["type_name"], cbucket["name"]),
            try:
                mdlbucket = ceph_models.Bucket.objects.get(cluster=cluster, ceph_id=cbucket["id"])
                print "known"
            except ceph_models.Bucket.DoesNotExist:
                mdltype   = ceph_models.Type.objects.get(cluster=cluster, ceph_id=cbucket["type_id"])
                mdlbucket = ceph_models.Bucket(cluster=cluster, ceph_id=cbucket["id"], type=mdltype,
                                            name=cbucket["name"], alg=cbucket["alg"], hash=cbucket["hash"])
                mdlbucket.full_clean()
                mdlbucket.save()
                print "added"

            # Now check dependencies.
            for member in cbucket["items"]:
                if member["id"] >= 0:
                    print "We're parent for OSD %d..." % member["id"],
                    for cdevice in crushmap["devices"]:
                        if cdevice["id"] == member["id"]:
                            osdbuckets[ cdevice["name"] ] = mdlbucket
                            print "found"
                            break
                    else:
                        print "not found"
                    continue

                print "We're parent for Bucket %d..." % member["id"],
                try:
                    mdlmember = ceph_models.Bucket.objects.get(cluster=cluster, ceph_id=member["id"])
                except ceph_models.Bucket.DoesNotExist:
                    # Member bukkit has not yet been entered into the DB, so re-visit us later.
                    buckets.append(cbucket)
                    print "retry"
                    break
                else:
                    # Member is known, set the parent field.
                    if mdlmember.parent != mdlbucket:
                        mdlmember.parent = mdlbucket
                        mdlmember.full_clean()
                        mdlmember.save()
                        print "added"
                    else:
                        print "known"

        for crule in crushmap["rules"]:
            print "Checking ceph ruleset %s..." % crule["rule_name"],
            try:
                mdlrule = ceph_models.Ruleset.objects.get(cluster=cluster, ceph_id=crule["ruleset"])
                print "known"
            except ceph_models.Ruleset.DoesNotExist:
                mdlrule = ceph_models.Ruleset(cluster=cluster, ceph_id=crule["ruleset"], name=crule["rule_name"],
                              type=crule["type"], min_size=crule["min_size"], max_size=crule["max_size"])
                mdlrule.full_clean()
                mdlrule.save()
                print "added"

        for cosd in osdmap["osds"]:
            print "Checking Ceph OSD %d..." % cosd["osd"],
            try:
                mdlosd = ceph_models.OSD.objects.get(cluster=cluster, ceph_id=cosd["osd"])
                print "known"
            except ceph_models.OSD.DoesNotExist:
                osdname = "osd.%d" % cosd["osd"]
                mdlosd = ceph_models.OSD(cluster=cluster, ceph_id=cosd["osd"], uuid=cosd["uuid"], bucket=osdbuckets[osdname])
                mdlosd.full_clean()
                mdlosd.save()
                print "added"

            # If the volume is unknown and this is a local OSD, let's see if we can update that
            osdpath = os.path.join("/var/lib/ceph/osd", "%s-%d" % (mdlosd.cluster.displayname, mdlosd.ceph_id))
            if ((mdlosd.volume is None or mdlosd.journal is None) and
                os.path.exists(osdpath) and os.path.islink(osdpath)):
                volumepath = os.readlink(osdpath)
                journalpath = os.path.join(osdpath, "journal")
                if os.path.exists(journalpath) and os.path.islink(journalpath):
                    journaldevpath = os.readlink(journalpath)
                else:
                    journaldevpath = ""
                dirty = False
                for fsv_so in StorageObject.objects.filter(filesystemvolume__isnull=False):
                    if volumepath.startswith(fsv_so.filesystemvolume.volume.path):
                        mdlosd.volume = fsv_so.filesystemvolume.volume
                        dirty = True
                        break
                for bv_so in StorageObject.objects.filter(blockvolume__isnull=False):
                    if volumepath.startswith(bv_so.blockvolume.volume.path):
                        mdlosd.journal = bv_so.blockvolume.volume
                        dirty = True
                        break
                if dirty:
                    mdlosd.full_clean()
                    mdlosd.save()

        for cpool in osdmap["pools"]:
            print "Checking Ceph pool %s..." % cpool["pool_name"],
            mdlrule = ceph_models.Ruleset.objects.get(cluster=cluster, ceph_id=cpool["crush_ruleset"])
            try:
                mdlpool = ceph_models.Pool.objects.get(cluster=cluster, ceph_id=cpool["pool"])
                print "known"
                mdlpool.ruleset = mdlrule
                mdlpool.save()
            except ceph_models.Pool.DoesNotExist:
                storageobj = StorageObject(name=cpool["pool_name"], megs=df["stats"]["total_space"] / 1024)
                storageobj.full_clean()
                storageobj.save()
                mdlpool = ceph_models.Pool(cluster=cluster, ceph_id=cpool["pool"], storageobj=storageobj, size=cpool["size"],
                              ruleset=mdlrule, min_size=cpool["min_size"])
                mdlpool.full_clean()
                mdlpool.save()
                print "added"

        iprgx = re.compile(r"^(?P<ip>.+):(?P<port>\d+)/\d+$")
        for cmds in mds_stat["mdsmap"]["info"].values():
            print "Checking Ceph mds %s..." % cmds["name"],

            m = iprgx.match(cmds["addr"])
            try:
                ip = IPAddress.objects.get(address__startswith=m.group("ip"))
            except IPAddress.DoesNotExist:
                print "Host unknown, ignored"
                continue

            try:
                mdlmds = ceph_models.MDS.objects.get(cluster=cluster, host=ip.device.host)
                print "found"
            except ceph_models.MDS.DoesNotExist:
                mdlmds = ceph_models.MDS(cluster=cluster, host=ip.device.host)
                mdlmds.full_clean()
                mdlmds.save()
                print "added"

        for cmon in mon_stat["monmap"]["mons"]:
            print "Checking Ceph mon %s..." % cmon["name"],

            m = iprgx.match(cmon["addr"])
            try:
                ip = IPAddress.objects.get(address__startswith=m.group("ip"))
            except IPAddress.DoesNotExist:
                print "Host unknown, ignored"
                continue

            try:
                mdlmon = ceph_models.Mon.objects.get(cluster=cluster, host=ip.device.host)
                print "found"
            except ceph_models.Mon.DoesNotExist:
                mdlmon = ceph_models.Mon(cluster=cluster, host=ip.device.host)
                mdlmon.full_clean()
                mdlmon.save()
                print "added"

        for centity in auth_list["auth_dump"]:
            print "Checking Ceph auth entity %s..." % centity["entity"],

            try:
                mdlentity = ceph_models.Entity.objects.get(entity=centity["entity"])
                print "found"
            except ceph_models.Entity.DoesNotExist:
                mdlentity = ceph_models.Entity(cluster=cluster, entity=centity["entity"], key=centity["key"])
                mdlentity.full_clean()
                mdlentity.save()
                print "added"


sysutils.models.post_install.connect(update, sender=sysutils.models)
