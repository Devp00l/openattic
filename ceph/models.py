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

import json
import math

from django.db import models
from django.utils.translation import ugettext_noop as _
from django.core.exceptions import ValidationError

from systemd import get_dbus_object, dbus_to_python
from ifconfig.models import Host
from volumes.models import FileSystemVolume, VolumePool, BlockVolume

class Cluster(models.Model):
    AUTH_CHOICES = (
        ('none',  _('Authentication disabled')),
        ('cephx', _('CephX Authentication')),
        )

    uuid        = models.CharField(max_length=36, unique=True)
    displayname = models.CharField(max_length=250, default='', blank=True)
    auth_cluster_required   = models.CharField(max_length=10, default='cephx', choices=AUTH_CHOICES)
    auth_service_required   = models.CharField(max_length=10, default='cephx', choices=AUTH_CHOICES)
    auth_client_required    = models.CharField(max_length=10, default='cephx', choices=AUTH_CHOICES)

    def get_status(self):
        return json.loads(dbus_to_python(get_dbus_object("/ceph").status(self.displayname)))

    def df(self):
        return json.loads(dbus_to_python(get_dbus_object("/ceph").df(self.displayname)))

    def get_recommended_pg_num(self, repsize):
        """ Calculate the recommended number of PGs for a given repsize.

            See http://ceph.com/docs/master/rados/operations/placement-groups/ for details.
        """
        return int(2 ** math.ceil(math.log(( self.osd_set.count() * 100 / repsize ), 2)))

    @property
    def status(self):
        return self.get_status()["health"]["overall_status"]

    def __unicode__(self):
        return "'%s' (%s)" % (self.displayname, self.uuid)

class Type(models.Model):
    cluster     = models.ForeignKey(Cluster)
    ceph_id     = models.IntegerField()
    name        = models.CharField(max_length=50)

    class Meta:
        unique_together = (('cluster', 'ceph_id'), ('cluster', 'name'))

    def __unicode__(self):
        return "'%s' (%s)" % (self.name, self.ceph_id)

class Bucket(models.Model):
    cluster     = models.ForeignKey(Cluster)
    type        = models.ForeignKey(Type)
    ceph_id     = models.IntegerField()
    name        = models.CharField(max_length=50)
    parent      = models.ForeignKey('self', null=True, blank=True)
    alg         = models.CharField(max_length=50, default="straw",
                                   choices=(("uniform", "uniform"), ("list", "list"), ("tree", "tree"), ("straw", "straw")))
    hash        = models.CharField(max_length=50, default="rjenkins1")

    class Meta:
        unique_together = (('cluster', 'ceph_id'), ('cluster', 'name'))

    def __unicode__(self):
        return "'%s' (%s)" % (self.name, self.ceph_id)

class OSD(models.Model):
    cluster     = models.ForeignKey(Cluster)
    ceph_id     = models.IntegerField()
    uuid        = models.CharField(max_length=36, unique=True)
    bucket      = models.ForeignKey(Bucket)
    volume      = models.ForeignKey(FileSystemVolume, null=True, blank=True)
    journal     = models.ForeignKey(BlockVolume,      null=True, blank=True)

    class Meta:
        unique_together = (('cluster', 'ceph_id'),)

    def __unicode__(self):
        return "osd.%s (%s)" % (self.ceph_id, unicode(self.volume))

    def save( self, database_only=False, *args, **kwargs ):
        install = (self.id is None)
        super(OSD, self).save(*args, **kwargs)
        if install and not database_only:
            fspath = self.volume.volume.path
            jnldev = self.journal.volume.path if self.journal is not None else ""
            get_dbus_object("/ceph").format_volume_as_osd(self.rbd_pool.cluster.displayname, fspath, jnldev)

class Mon(models.Model):
    cluster     = models.ForeignKey(Cluster)
    host        = models.ForeignKey(Host)

    def __unicode__(self):
        return unicode(self.host)

class MDS(models.Model):
    cluster     = models.ForeignKey(Cluster)
    host        = models.ForeignKey(Host)

    def __unicode__(self):
        return unicode(self.host)

class Ruleset(models.Model):
    cluster     = models.ForeignKey(Cluster)
    ceph_id     = models.IntegerField()
    name        = models.CharField(max_length=250)
    type        = models.IntegerField(default=1)
    min_size    = models.IntegerField(default=1)
    max_size    = models.IntegerField(default=10)

class Pool(VolumePool):
    cluster     = models.ForeignKey(Cluster)
    ceph_id     = models.IntegerField()
    size        = models.IntegerField(default=3)
    min_size    = models.IntegerField(default=2)
    ruleset     = models.ForeignKey(Ruleset)

    class Meta:
        unique_together = (('cluster', 'ceph_id'),)

    def __unicode__(self):
        return unicode(self.storageobj.name)

    def full_clean(self):
        super(Pool, self).full_clean()
        if self.min_size > self.size:
            raise ValidationError({"min_size": ["min_size must be less than or equal to size"]})

    def save( self, database_only=False, *args, **kwargs ):
        install = (self.id is None)
        super(Pool, self).save(*args, **kwargs)
        if database_only:
            return
        if install:
            get_dbus_object("/ceph").osd_pool_create(self.cluster.displayname, self.storageobj.name,
                                                     self.cluster.get_recommended_pg_num(self.size),
                                                     self.ruleset.ceph_id)
        else:
            get_dbus_object("/ceph").osd_pool_set(self.cluster.displayname, self.storageobj.name, "size",          str(self.size))
            get_dbus_object("/ceph").osd_pool_set(self.cluster.displayname, self.storageobj.name, "min_size",      str(self.min_size))
            get_dbus_object("/ceph").osd_pool_set(self.cluster.displayname, self.storageobj.name, "crush_ruleset", str(self.ruleset.ceph_id))

    def delete(self):
        super(Pool, self).delete()
        get_dbus_object("/ceph").osd_pool_delete(self.cluster.displayname, self.storageobj.name)

    @property
    def usedmegs(self):
        for poolinfo in self.cluster.df()["pools"]:
            if poolinfo["name"] == self.storageobj.name:
                return int(poolinfo["stats"]["kb_used"] / 1024.)
        raise KeyError("pool not found in ceph df")

    @property
    def status(self):
        return self.cluster.status

    @property
    def host(self):
        return Host.objects.get_current()

    def is_fs_supported(self, filesystem):
        return True

    def _create_volume_for_storageobject(self, storageobj, options):
        image = Image(rbd_pool=self, storageobj=storageobj)
        image.full_clean()
        image.save()
        return image


class Entity(models.Model):
    cluster     = models.ForeignKey(Cluster)
    entity      = models.CharField(max_length=250)
    key         = models.CharField(max_length=50, blank=True)

    def save(self, database_only=False, *args, **kwargs ):
        if self.id is None and not database_only:
            get_dbus_object("/ceph").auth_add(self.cluster.displayname, self.entity)
            self.key = json.loads(get_dbus_object("/ceph").auth_get_key(self.cluster.displayname, self.entity))["key"]
        super(Entity, self).save(*args, **kwargs)

    def delete(self):
        super(Entity, self).delete()
        get_dbus_object("/ceph").auth_del(self.cluster.displayname, self.entity)

    def __unicode__(self):
        return self.entity


class Image(BlockVolume):
    rbd_pool    = models.ForeignKey(Pool)

    def save( self, database_only=False, *args, **kwargs ):
        if database_only:
            return BlockVolume.save(self, *args, **kwargs)
        install = (self.id is None)
        super(Image, self).save(*args, **kwargs)
        if install:
            get_dbus_object("/ceph").rbd_create(self.rbd_pool.cluster.displayname, self.rbd_pool.storageobj.name, self.storageobj.name, self.storageobj.megs)

    def delete(self):
        super(Image, self).delete()
        get_dbus_object("/ceph").rbd_rm(self.rbd_pool.cluster.displayname, self.rbd_pool.storageobj.name, self.storageobj.name)

    @property
    def host(self):
        return Host.objects.get_current()

    @property
    def status(self):
        if self.storageobj.is_locked:
            return "locked"
        return self.rbd_pool.status

    @property
    def path(self):
        return "/dev/rbd/%s/%s" % (self.rbd_pool.storageobj.name, self.storageobj.name)
