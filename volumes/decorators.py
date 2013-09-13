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

from django.db.models import signals
from django.contrib.contenttypes.models import ContentType

from volumes import models

def _create_blkvolume(instance, **kwargs):
    blkvolumetype = ContentType.objects.get_for_model(instance.__class__)
    try:
        blkvolume = models.BlockVolume.objects.get(content_type=blkvolumetype, object_id=instance.id)
    except models.BlockVolume.DoesNotExist:
        blkvolume = models.BlockVolume()
        blkvolume.volume = instance
        blkvolume.capflags = 0
        blkvolume.save()

def _delete_blkvolume(instance, **kwargs):
    blkvolumetype = ContentType.objects.get_for_model(instance.__class__)
    try:
        blkvolume = models.BlockVolume.objects.get(content_type=blkvolumetype, object_id=instance.id)
    except models.BlockVolume.DoesNotExist:
        pass
    else:
        blkvolume.delete()

def BlockVolume(model):
    signals.post_save.connect(  _create_blkvolume, sender=model )
    signals.pre_delete.connect( _delete_blkvolume, sender=model )
    return model

def _create_fsvolume(instance, **kwargs):
    fsvolumetype = ContentType.objects.get_for_model(instance.__class__)
    try:
        fsvolume = models.BlockVolume.objects.get(content_type=fsvolumetype, object_id=instance.id)
    except models.FileSystemVolume.DoesNotExist:
        fsvolume = models.FileSystemVolume()
        fsvolume.volume = instance
        fsvolume.capflags = 0
        fsvolume.save()

def _delete_fsvolume(instance, **kwargs):
    fsvolumetype = ContentType.objects.get_for_model(instance.__class__)
    try:
        fsvolume = models.BlockVolume.objects.get(content_type=fsvolumetype, object_id=instance.id)
    except models.FileSystemVolume.DoesNotExist:
        pass
    else:
        fsvolume.delete()

def FileSystemVolume(model):
    signals.post_save.connect(  _create_fsvolume, sender=model )
    signals.pre_delete.connect( _delete_fsvolume, sender=model )
    return model
