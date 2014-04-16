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


from django.db import models

from ifconfig.models import Host, HostDependentManager, getHostDependentManagerClass
from volumes.models import InvalidVolumeType, StorageObject, VolumePool, FileSystemVolume, CapabilitiesAwareManager

from btrfs import filesystems


class Btrfs(VolumePool):
    host        = models.ForeignKey(Host)

    objects     = HostDependentManager()
    all_objects = models.Manager()

    @property
    def fullname(self):
        return self.storageobj.name

    @property
    def fs(self):
        return filesystems.Btrfs(self, self.storageobj.filesystemvolume.volume)

    @property
    def status(self):
        return "online"

    @property
    def usedmegs(self):
        return self.fs.stat["used"]

    def _create_volume_for_storageobject(self, storageobj, options):
        if options.get("filesystem", None) not in ("btrfs", None):
            raise InvalidVolumeType(options.get("filesystem", None))
        if "filesystem" in options:
            options = options.copy()
            del options["filesystem"]
        storageobj.megs = self.storageobj.megs
        storageobj.save()
        sv = BtrfsSubvolume(storageobj=storageobj, btrfs=self, parent=self.storageobj, **options)
        sv.full_clean()
        sv.save()
        return sv

    def is_fs_supported(self, filesystem):
        return filesystem is filesystems.Btrfs


class BtrfsSubvolume(FileSystemVolume):
    btrfs       = models.ForeignKey(Btrfs)
    parent      = models.ForeignKey(StorageObject, blank=True, null=True)

    objects     = getHostDependentManagerClass("btrfs__host")()
    all_objects = models.Manager()
    fstype      = "btrfs"

    def save(self, *args, **kwargs):
        install = (self.id is None)
        if self.btrfs_id is None and self.pool is not None:
            self.btrfs = self.pool.volumepool
        FileSystemVolume.save(self, *args, **kwargs)
        if install:
            if self.parent is None:
                self.fs.format()
            elif self.storageobj.snapshot is not None:
                # the volume represented by self is supposed to be a snapshot of the
                # btrfs subvolume that my storageobj's "snapshot" attribute points to.
                origin = self.storageobj.snapshot.filesystemvolume.volume
                if not isinstance(origin, BtrfsSubvolume):
                    raise TypeError("btrfs can only snapshot btrfs subvolumes")
                self.fs.create_snapshot(origin, False)
            else:
                self.fs.create_subvolume()
            self.fs.chown()

    def delete(self):
        if self.parent is None:
            self.fs.unmount()
        else:
            self.fs.delete_subvolume()
        FileSystemVolume.delete(self)

    @property
    def fs(self):
        return filesystems.Btrfs(self.btrfs, self)

    @property
    def status(self):
        return self.btrfs.status

    @property
    def usedmegs(self):
        return self.fs.stat["used"]

    @property
    def host(self):
        return self.btrfs.host

    @property
    def fullname(self):
        if self.parent is not None:
            parentname = self.parent.filesystemvolume.volume.fullname
            return "%s/%s" % (parentname, self.storageobj.name)
        return self.storageobj.name

    def _create_snapshot_for_storageobject(self, storageobj, options):
        sv = BtrfsSubvolume(storageobj=storageobj, btrfs=self.btrfs, parent=self.parent,
                            fswarning=self.fswarning, fscritical=self.fscritical, owner=self.owner)
        sv.full_clean()
        sv.save()
        return sv

    def __unicode__(self):
        return self.fullname
