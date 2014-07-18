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

import os.path

from django.db import models

from ifconfig.models import Host, HostDependentManager, getHostDependentManagerClass
from volumes.models import InvalidVolumeType, StorageObject, VolumePool, BlockVolume, FileSystemVolume, CapabilitiesAwareManager

from zfs import filesystems


class Zpool(VolumePool):
    host        = models.ForeignKey(Host)

    objects     = HostDependentManager()
    all_objects = models.Manager()

    @property
    def fs(self):
        return filesystems.Zfs(self, self.storageobj.filesystemvolume.volume)

    @property
    def status(self):
        if self.storageobj.is_locked:
            return "locked"
        return self.fs.status

    @property
    def usedmegs(self):
        import dbus
        try:
            # This may fail when we're trying to query for a volumepool which
            # has not yet been created
            return self.fs.allocated_megs
        except dbus.DBusException:
            return None

    def _create_volume_for_storageobject(self, storageobj, options):
        if options.get("filesystem", None) not in ("zfs", '', None):
            raise InvalidVolumeType(options.get("filesystem", None))

        if not options.get("filesystem", None):
            zvol = ZVol(storageobj=storageobj, zpool=self)
            zvol.full_clean()
            zvol.save()
            return zvol
        else:
            if "filesystem" in options:
                options = options.copy()
                del options["filesystem"]

            zfs = Zfs(storageobj=storageobj, zpool=self, parent=self.storageobj, **options)
            zfs.full_clean()
            zfs.save()
            return zfs

    def is_fs_supported(self, filesystem):
        return filesystem is filesystems.Zfs


class RaidZ(models.Model):
    name        = models.CharField(max_length=150)
    zpool       = models.ForeignKey(Zpool)
    type        = models.CharField(max_length=150)


class Zfs(FileSystemVolume):
    zpool       = models.ForeignKey(Zpool)
    parent      = models.ForeignKey(StorageObject, blank=True, null=True)

    objects     = getHostDependentManagerClass("zpool__host")()
    all_objects = models.Manager()

    def save(self, database_only=False, *args, **kwargs):
        if database_only:
            return FileSystemVolume.save(self, *args, **kwargs)
        install = (self.id is None)
        FileSystemVolume.save(self, *args, **kwargs)
        if install:
            if self.parent is None:
                self.fs.format()
            elif self.storageobj.snapshot is not None:
                # the volume represented by self is supposed to be a snapshot of the
                # zfs subvolume that my storageobj's "snapshot" attribute points to.
                origin = self.storageobj.snapshot.filesystemvolume.volume
                if not isinstance(origin, Zfs):
                    raise TypeError("zfs can only snapshot zfs volumes, got '%s' instead" % unicode(origin))
                self.fs.create_snapshot(origin)
            else:
                self.fs.create_subvolume()
                self.fs.chown()

    def delete(self):
        FileSystemVolume.delete(self)
        if self.parent is None:
            self.fs.destroy()
        elif self.storageobj.snapshot is not None:
            origin = self.storageobj.snapshot.filesystemvolume.volume
            self.fs.destroy_snapshot(origin)
        else:
            self.fs.destroy_subvolume()

    def full_clean(self):
        FileSystemVolume.full_clean(self)
        # free space is irrelevant for a Zfs because it's just a quota, not a
        # real size limit
        if float(self.zpool.storageobj.megs) < int(self.storageobj.megs):
            from django.core.exceptions import ValidationError
            raise ValidationError({"megs": ["ZPool %s has insufficient space (%f < %d)." % (
                self.zpool.storageobj.name, self.zpool.storageobj.megs, self.storageobj.megs)]})

    @property
    def fs(self):
        return filesystems.Zfs(self.zpool, self)

    @property
    def status(self):
        if self.storageobj.is_locked:
            return "locked"
        return self.zpool.status

    @property
    def host(self):
        return self.zpool.host

    @property
    def fullname(self):
        if self.parent is not None:
            parentname = self.parent.filesystemvolume.volume.fullname
            return "%s/%s" % (parentname, self.storageobj.name)
        return self.storageobj.name

    @property
    def usedmegs(self):
        return self.fs.stat["used"]

    def _create_snapshot_for_storageobject(self, storageobj, options):
        if self.parent is not None:
            snapparent = self.parent
        else:
            snapparent = self.zpool.storageobj
        sv = Zfs(storageobj=storageobj, zpool=self.zpool, parent=snapparent,
                 fswarning=self.fswarning, fscritical=self.fscritical, owner=self.owner)
        sv.full_clean()
        sv.save()
        return sv

    def __unicode__(self):
        return self.fullname


class ZVol(BlockVolume):
    zpool       = models.ForeignKey(Zpool)

    objects     = getHostDependentManagerClass("zpool__host")()
    all_objects = models.Manager()

    def save(self, database_only=False, *args, **kwargs):
        if database_only:
            return BlockVolume.save(self, *args, **kwargs)
        install = (self.id is None)
        BlockVolume.save(self, *args, **kwargs)
        if install:
            if self.storageobj.snapshot is not None:
                # the volume represented by self is supposed to be a snapshot of the
                # zfs subvolume that my storageobj's "snapshot" attribute points to.
                origin = self.storageobj.snapshot.blockvolume.volume
                if not isinstance(origin, ZVol):
                    raise TypeError("zfs can only snapshot zfs volumes, got '%s' instead" % unicode(origin))
                self.fs.create_zvol_snapshot(origin)
            else:
                self.fs.create_zvol()

    def delete(self):
        BlockVolume.delete(self)
        if self.storageobj.snapshot is not None:
            origin = self.storageobj.snapshot.blockvolume.volume
            self.fs.destroy_snapshot(origin)
        else:
            self.fs.destroy_subvolume()

    def full_clean(self):
        BlockVolume.full_clean(self)
        currmegs = 0
        if self.id is not None:
            currmegs = ZVol.objects.get(id=self.id).storageobj.megs
        unalloced_megs = self.zpool.storageobj.megs - float(self.zpool.fs.rootfs_used_megs)
        if unalloced_megs < int(self.storageobj.megs) - currmegs:
            from django.core.exceptions import ValidationError
            raise ValidationError({"megs": ["ZPool %s has insufficient free space (%f < %d)." % (
                self.zpool.storageobj.name, unalloced_megs, self.storageobj.megs - currmegs)]})

    @property
    def fs(self):
        return filesystems.Zfs(self.zpool, self)

    @property
    def path(self):
        return os.path.join("/dev", self.fullname)

    @property
    def status(self):
        if self.storageobj.is_locked:
            return "locked"
        return self.zpool.status

    @property
    def host(self):
        return self.zpool.host

    @property
    def fullname(self):
        if self.storageobj.snapshot is not None:
            return "%s@%s" % (self.storageobj.snapshot.blockvolume.volume.fullname, self.storageobj.name)
        return "%s/%s" % (self.zpool.storageobj.name, self.storageobj.name)

    @property
    def usedmegs(self):
        return self.fs.stat["used"]

    def _create_snapshot_for_storageobject(self, storageobj, options):
        sv = ZVol(storageobj=storageobj, zpool=self.zpool)
        sv.full_clean()
        sv.save()
        return sv

    def __unicode__(self):
        return self.fullname

    def shrink( self, oldmegs, newmegs ):
        self.fs.set_zvol_size(newmegs)

    def grow( self, oldmegs, newmegs ):
        self.fs.set_zvol_size(newmegs)
