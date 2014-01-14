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

import uuid

from django.contrib.auth.models import User
from django.db import models

class APIKey(models.Model):
    apikey      = models.CharField( max_length=40 )
    owner       = models.ForeignKey( User, blank=True, null=True )
    description = models.CharField( max_length=250 )
    active      = models.BooleanField( default=True, blank=True )

    def full_clean(self):
        if not self.apikey:
            self.apikey = unicode(uuid.uuid4())
        return models.Model.full_clean(self)
