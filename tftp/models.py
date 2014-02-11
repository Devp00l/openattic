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

from django.db   import models

from systemd import get_dbus_object
from ifconfig.models import getHostDependentManagerClass, IPAddress
from volumes.models import FileSystemVolume

class Instance(models.Model):
    volume      = models.ForeignKey(FileSystemVolume)
    path        = models.CharField(max_length=255)
    address     = models.ForeignKey(IPAddress, unique=True)

    share_type  = "tftp"
    objects     = getHostDependentManagerClass("volume__volume__host")()
    all_objects = models.Manager()

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.volume.filesystem:
            raise ValidationError('This share type can only be used on volumes with a file system.')

    def save( self, *args, **kwargs ):
        ret = models.Model.save(self, *args, **kwargs)
        tftp = get_dbus_object("/tftp")
        tftp.writeconf()
        tftp.reload()
        return ret

    def delete( self ):
        ret = models.Model.delete(self)
        tftp = get_dbus_object("/tftp")
        tftp.writeconf()
        tftp.reload()
        return ret
